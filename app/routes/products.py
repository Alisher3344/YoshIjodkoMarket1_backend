from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..core.database import get_db
from ..core.security import get_current_user
from ..crud import product as product_crud
from ..models.product import Product
from ..models.user import User
from ..schemas.product import ProductCreate

router = APIRouter()


def product_to_dict(p: Product, user: User = None) -> dict:
    """Product + user avatar birgalikda"""
    d = {
        "id":           p.id,
        "name_uz":      p.name_uz,
        "name_ru":      p.name_ru,
        "desc_uz":      p.desc_uz,
        "desc_ru":      p.desc_ru,
        "price":        p.price,
        "old_price":    p.old_price,
        "stock":        p.stock,
        "category":     p.category,
        "badge":        p.badge,
        "author":       p.author,
        "author_ru":    p.author_ru,
        "school":       p.school,
        "school_ru":    p.school_ru,
        "grade":        p.grade,
        "district":     p.district,
        "district_ru":  p.district_ru,
        "region":       p.region,
        "region_ru":    p.region_ru,
        "phone":        p.phone,
        "student_type": p.student_type,
        "card_number":  p.card_number,
        "story_uz":     p.story_uz,
        "story_ru":     p.story_ru,
        "photo":        p.photo,
        "image":        p.image,
        "rating":       p.rating,
        "reviews":      p.reviews,
        "sold":         p.sold,
        "user_id":      p.user_id,
        # Muallif haqida
        "author_avatar": user.avatar if user else "",
        "illness_info":  user.illness_info if user and user.is_disabled else "",
        "full_name":     user.full_name if user else "",
    }
    return d


@router.get("/")
async def get_products(
    category: Optional[str] = Query(None),
    search:   Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Hamma mahsulotlar — faqat stock > 0 bo'lganlari (asosiy sayt)"""
    query = select(Product).where(Product.stock > 0)
    if category and category != "all":
        query = query.where(Product.category == category)
    if search:
        query = query.where(Product.name_uz.ilike(f"%{search}%"))
    query = query.order_by(Product.id.desc())

    result = await db.execute(query)
    products = result.scalars().all()

    # Har bir mahsulot uchun user ni olish
    response = []
    for p in products:
        user = None
        if p.user_id:
            u_res = await db.execute(select(User).where(User.id == p.user_id))
            user = u_res.scalar_one_or_none()
        response.append(product_to_dict(p, user))

    return response


@router.get("/my")
async def get_my_products(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """O'z kabinetdagi mahsulotlar — stock = 0 bo'lganlari ham ko'rinadi"""
    result = await db.execute(
        select(Product).where(Product.user_id == current_user.id).order_by(Product.id.desc())
    )
    products = result.scalars().all()

    return [product_to_dict(p, current_user) for p in products]


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    user = None
    if product.user_id:
        u_res = await db.execute(select(User).where(User.id == product.user_id))
        user = u_res.scalar_one_or_none()

    return product_to_dict(product, user)


@router.post("/")
async def create_product(
    data: ProductCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Yangi mahsulot qo'shish"""
    d = data.model_dump()

    if current_user.is_disabled:
        d["student_type"] = "disabled"
        if current_user.card_number and not d.get("card_number"):
            d["card_number"] = current_user.card_number

    if not d.get("author"):
        d["author"] = current_user.full_name or current_user.name
    if not d.get("school"):
        d["school"] = current_user.school or ""

    # Avtor profil rasmi va kasallik haqida
    if current_user.avatar and not d.get("photo"):
        d["photo"] = current_user.avatar
    if current_user.illness_info and not d.get("story_uz"):
        d["story_uz"] = current_user.illness_info

    product = Product(**d, user_id=current_user.id)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product_to_dict(product, current_user)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    data: ProductCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    is_admin = current_user.role in ("admin", "superadmin")
    if product.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Siz bu mahsulotning egasi emassiz")

    await product_crud.update(db, product, data)

    user = None
    if product.user_id:
        u_res = await db.execute(select(User).where(User.id == product.user_id))
        user = u_res.scalar_one_or_none()

    return product_to_dict(product, user)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    is_admin = current_user.role in ("admin", "superadmin")
    if product.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Siz bu mahsulotning egasi emassiz")

    await product_crud.delete(db, product)
    return {"success": True}
@router.get("/user/{user_id}")
async def get_products_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Ma'lum user mahsulotlari — muallif sahifasi uchun"""
    result = await db.execute(
        select(Product)
        .where(Product.user_id == user_id)
        .where(Product.stock > 0)
        .order_by(Product.id.desc())
    )
    products = result.scalars().all()

    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()

    return [product_to_dict(p, user) for p in products]