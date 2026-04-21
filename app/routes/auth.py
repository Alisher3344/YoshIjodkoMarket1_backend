import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import create_access_token, get_current_user, hash_password, verify_password
from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest
from ..schemas.user import ProfileUpdate

router = APIRouter()


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    return re.sub(r'[^\d+]', '', phone)


def user_dict(u: User) -> dict:
    return {
        "id":           u.id,
        "name":         u.name,
        "full_name":    u.full_name or "",
        "username":     u.username,
        "phone":        u.phone or "",
        "school":       u.school or "",
        "age":          u.age or 0,
        "is_disabled":  u.is_disabled,
        "card_number":  u.card_number or "",
        "illness_info": u.illness_info or "",
        "avatar":       u.avatar or "",
        "role":         u.role,
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
    phone_clean = normalize_phone(data.phone)
    if not phone_clean:
        raise HTTPException(status_code=400, detail="Telefon raqami noto'g'ri")

    result = await db.execute(select(User).where(User.username == phone_clean))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu telefon raqami allaqachon ro'yxatdan o'tgan")

    user = User(
        name         = data.name.strip(),
        full_name    = "",
        username     = phone_clean,
        phone        = phone_clean,
        password     = hash_password(data.password),
        school       = data.school or "",
        age          = data.age or 0,
        is_disabled  = bool(data.is_disabled),
        card_number  = data.card_number if data.is_disabled else "",
        illness_info = "",
        avatar       = "",
        role         = "student",
        active       = True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user": user_dict(user)}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return user_dict(current_user)

@router.get("/my-sales")
async def my_sales(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Foydalanuvchining sotilgan mahsulotlari (o'z mahsulotlariga kelgan buyurtmalar)"""
    from ..models.order import Order, OrderItem
    from ..models.product import Product
    from sqlalchemy.orm import selectinload

    # Foydalanuvchining mahsulotlari ID lari
    prod_res = await db.execute(
        select(Product.id).where(Product.user_id == current_user.id)
    )
    product_ids = [row[0] for row in prod_res.all()]

    if not product_ids:
        return []

    # Shu mahsulotlarga tegishli order_items
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

@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Foydalanuvchi o'z profilini yangilaydi"""
    current_user.name         = data.name.strip()
    current_user.full_name    = data.full_name or ""
    current_user.school       = data.school or ""
    current_user.age          = data.age or 0
    current_user.illness_info = data.illness_info or ""
    current_user.avatar       = data.avatar or ""

    # Agar imkoniyati cheklangan bo'lsa — karta raqami
    if current_user.is_disabled:
        current_user.card_number = data.card_number or ""

    await db.flush()
    await db.refresh(current_user)
    return user_dict(current_user)