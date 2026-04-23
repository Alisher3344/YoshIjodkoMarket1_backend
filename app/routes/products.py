from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import get_current_user
from ..crud import product as product_crud
from ..models.product import Product
from ..models.user import User
from ..models.student import Student
from ..schemas.product import ProductCreate

router = APIRouter()


def product_to_dict(p: Product, user: User = None, student: Student = None) -> dict:
    """Product + admin va student ma'lumotlari birgalikda"""
    # Avtor ma'lumotlari — avval student (agar bog'langan bo'lsa), keyin user
    author_avatar = ""
    full_name = ""
    illness_info = ""

    if student:
        author_avatar = student.avatar or ""
        full_name = student.full_name or student.name or ""
        if student.is_disabled:
            illness_info = student.illness_info or ""
    elif user:
        author_avatar = user.avatar or ""
        full_name = user.full_name or ""
        if user.is_disabled:
            illness_info = user.illness_info or ""

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
        "student_id":   p.student_id,
        # Muallif haqida
        "author_avatar": author_avatar,
        "illness_info":  illness_info,
        "full_name":     full_name,
    }
    return d


async def _fetch_author_info(db: AsyncSession, product: Product):
    """Student va user ma'lumotlarini olish"""
    student = None
    user = None

    if product.student_id:
        s_res = await db.execute(select(Student).where(Student.id == product.student_id))
        student = s_res.scalar_one_or_none()

    if product.user_id:
        u_res = await db.execute(select(User).where(User.id == product.user_id))
        user = u_res.scalar_one_or_none()

    return user, student


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

    response = []
    for p in products:
        user, student = await _fetch_author_info(db, p)
        response.append(product_to_dict(p, user, student))

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

    response = []
    for p in products:
        student = None
        if p.student_id:
            s_res = await db.execute(select(Student).where(Student.id == p.student_id))
            student = s_res.scalar_one_or_none()
        response.append(product_to_dict(p, current_user, student))

    return response


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    user, student = await _fetch_author_info(db, product)
    return product_to_dict(product, user, student)


@router.post("/")
async def create_product(
    data: ProductCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Yangi mahsulot qo'shish"""
    d = data.model_dump()

    # Agar student_id berilgan bo'lsa — student ma'lumotlarini avtomatik to'ldirish
    student = None
    if d.get("student_id"):
        s_res = await db.execute(select(Student).where(Student.id == d["student_id"]))
        student = s_res.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
        # Admin bu o'quvchini o'zi yaratganini tekshirish
        if student.admin_id != current_user.id and current_user.role != "superadmin":
            raise HTTPException(status_code=403, detail="Bu sizning o'quvchingiz emas")

        # Ma'lumotlarni student'dan to'ldirish
        if student.is_disabled:
            d["student_type"] = "disabled"
            if not d.get("card_number"):
                d["card_number"] = student.card_number or ""

        if not d.get("author"):
            d["author"] = student.full_name or student.name
        if not d.get("author_ru"):
            d["author_ru"] = student.name_ru or student.name
        if not d.get("school"):
            d["school"] = student.school or ""
        if not d.get("school_ru"):
            d["school_ru"] = student.school_ru or ""
        if not d.get("district"):
            d["district"] = student.district or ""
        if not d.get("region"):
            d["region"] = student.region or ""
        if not d.get("grade"):
            d["grade"] = student.grade or ""
        if not d.get("phone"):
            d["phone"] = student.phone or ""
        if not d.get("photo"):
            d["photo"] = student.avatar or ""
        if student.illness_info and not d.get("story_uz"):
            d["story_uz"] = student.illness_info
    else:
        # Eski rejim — user o'zi mahsulot qo'shsa
        if current_user.is_disabled:
            d["student_type"] = "disabled"
            if current_user.card_number and not d.get("card_number"):
                d["card_number"] = current_user.card_number

        if not d.get("author"):
            d["author"] = current_user.full_name or current_user.name
        if not d.get("school"):
            d["school"] = current_user.school or ""

        if current_user.avatar and not d.get("photo"):
            d["photo"] = current_user.avatar
        if current_user.illness_info and not d.get("story_uz"):
            d["story_uz"] = current_user.illness_info

    product = Product(**d, user_id=current_user.id)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product_to_dict(product, current_user, student)


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

    user, student = await _fetch_author_info(db, product)
    return product_to_dict(product, user, student)


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

    response = []
    for p in products:
        student = None
        if p.student_id:
            s_res = await db.execute(select(Student).where(Student.id == p.student_id))
            student = s_res.scalar_one_or_none()
        response.append(product_to_dict(p, user, student))

    return response