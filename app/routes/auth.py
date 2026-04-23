import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import create_access_token, get_current_user, verify_password
from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest
from ..schemas.user import ProfileUpdate
from ..core.security import hash_password

router = APIRouter()


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)


def user_dict(u: User) -> dict:
    return {
        "id":        u.id,
        "name":      u.name or "",
        "full_name": u.full_name or "",
        "username":  u.username,
        "phone":     u.phone or "",
        "school":    u.school or "",
        "avatar":    u.avatar or "",
        "role":      u.role,
    }


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    username = data.username.strip()
    if any(c.isdigit() for c in username):
        username = normalize_phone(username)

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")
    if not user.active:
        raise HTTPException(status_code=403, detail="Hisob bloklangan")

    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user": user_dict(user)}


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    name = (data.name or "").strip()
    full_name = (data.full_name or "").strip()
    password = data.password or ""
    phone_raw = data.phone or ""

    if not name:
        raise HTTPException(status_code=400, detail="Ism kiritilishi shart")
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak",
        )

    phone_digits = re.sub(r"\D", "", phone_raw)
    if len(phone_digits) != 12 or not phone_digits.startswith("998"):
        raise HTTPException(
            status_code=400,
            detail="Telefon raqam to'liq emas (+998 XX XXX XX XX)",
        )

    username = phone_digits  # username sifatida toza telefon raqami
    phone_pretty = f"+{phone_digits[:3]} {phone_digits[3:5]} {phone_digits[5:8]} {phone_digits[8:10]} {phone_digits[10:12]}"

    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Bu telefon raqam allaqachon ro'yxatdan o'tgan",
        )

    user = User(
        name=name,
        full_name=full_name,
        username=username,
        phone=phone_pretty,
        password=hash_password(password),
        role="user",
        active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user": user_dict(user)}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return user_dict(current_user)


@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin o'z profilini yangilaydi (faqat yuborilgan fieldlar)"""
    payload = data.model_dump(exclude_unset=True)

    for key, value in payload.items():
        if value is not None:
            setattr(current_user, key, value)

    await db.flush()
    await db.refresh(current_user)
    return user_dict(current_user)


@router.get("/my-sales")
async def my_sales(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from ..models.order import Order, OrderItem
    from ..models.product import Product
    from sqlalchemy.orm import selectinload

    prod_res = await db.execute(
        select(Product.id).where(Product.user_id == current_user.id)
    )
    product_ids = [row[0] for row in prod_res.all()]
    if not product_ids:
        return []

    items_res = await db.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.order))
        .where(OrderItem.product_id.in_(product_ids))
        .order_by(OrderItem.id.desc())
    )
    items = items_res.scalars().all()

    result = []
    for item in items:
        o = item.order
        result.append({
            "id":             item.id,
            "order_id":       o.id,
            "product_id":     item.product_id,
            "name_uz":        item.name_uz,
            "name_ru":        item.name_ru,
            "price":          item.price,
            "qty":            item.qty,
            "image":          item.image,
            "customer_name":  o.customer_name,
            "customer_phone": o.customer_phone,
            "status":         o.status,
            "created_at":     o.created_at.isoformat() if o.created_at else None,
            "total_price":    item.price * item.qty,
        })
    return result