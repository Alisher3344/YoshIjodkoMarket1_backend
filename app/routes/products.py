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
from ..models.school import School
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
        "status":       p.status,
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
    """Hamma mahsulotlar — faqat stock > 0 va status='approved' bo'lganlari (asosiy sayt)"""
    query = select(Product).where(
        Product.stock > 0, Product.status == "approved"
    )
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
    """O'z kabinetdagi mahsulotlar — stock = 0 bo'lganlari ham ko'rinadi.
    Agar admin maktabga biriktirilgan bo'lsa — shu maktabning hamma o'quvchilari mahsulotlarini ham qaytaradi
    (bir maktab adminlari umumiy ma'lumot ko'radi)."""
    if current_user.school_id:
        # Maktab adminlari: o'zi yaratganlari + maktab studentlariga tegishli mahsulotlar
        sub = select(Student.id).where(Student.school_id == current_user.school_id)
        student_ids = [r[0] for r in (await db.execute(sub)).all()]
        from sqlalchemy import or_
        cond = or_(Product.user_id == current_user.id)
        if student_ids:
            cond = or_(cond, Product.student_id.in_(student_ids))
        result = await db.execute(
            select(Product).where(cond).order_by(Product.id.desc())
        )
    else:
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
        # Admin bu o'quvchini boshqara olishini tekshirish:
        # superadmin / o'zi yaratgan / bir xil maktab adminlari ruxsat oladi
        can = (
            current_user.role == "superadmin"
            or student.admin_id == current_user.id
            or (
                student.school_id is not None
                and current_user.school_id is not None
                and student.school_id == current_user.school_id
            )
        )
        if not can:
            raise HTTPException(status_code=403, detail="Bu sizning maktabingiz o'quvchisi emas")

        # Ma'lumotlarni student'dan to'ldirish
        if student.is_disabled:
            d["student_type"] = "disabled"
            if not d.get("card_number"):
                d["card_number"] = student.card_number or ""

        if not d.get("author"):
            d["author"] = student.full_name or student.name
        if not d.get("author_ru"):
            d["author_ru"] = student.name_ru or student.name
        if not d.get("grade"):
            d["grade"] = student.grade or ""
        if not d.get("phone"):
            d["phone"] = student.phone or ""
        if not d.get("photo"):
            d["photo"] = student.avatar or ""
        if student.illness_info and not d.get("story_uz"):
            d["story_uz"] = student.illness_info

        # Maktab / Tuman / Viloyat — ustuvor ravishda admin'ning biriktirilgan maktabidan
        # (student'da bo'lsa fallback)
        school_obj = None
        if current_user.school_id:
            sch_res = await db.execute(
                select(School).where(School.id == current_user.school_id)
            )
            school_obj = sch_res.scalar_one_or_none()

        if not d.get("school"):
            d["school"] = (
                (school_obj.name if school_obj else None)
                or student.school
                or current_user.school
                or ""
            )
        if not d.get("school_ru"):
            d["school_ru"] = (
                (school_obj.name_ru if school_obj else None)
                or student.school_ru
                or ""
            )
        if not d.get("district"):
            d["district"] = (
                (school_obj.district if school_obj else None)
                or student.district
                or ""
            )
        if not d.get("region"):
            d["region"] = (
                (school_obj.region if school_obj else None)
                or student.region
                or ""
            )
    else:
        # Eski rejim — user o'zi mahsulot qo'shsa
        if current_user.is_disabled:
            d["student_type"] = "disabled"
            if current_user.card_number and not d.get("card_number"):
                d["card_number"] = current_user.card_number

        if not d.get("author"):
            d["author"] = current_user.full_name or current_user.name

        # Admin'ning biriktirilgan maktabidan school/district/region (ustuvor)
        school_obj = None
        if current_user.school_id:
            sch_res = await db.execute(
                select(School).where(School.id == current_user.school_id)
            )
            school_obj = sch_res.scalar_one_or_none()

        if not d.get("school"):
            d["school"] = (
                (school_obj.name if school_obj else None)
                or current_user.school
                or ""
            )
        if not d.get("school_ru") and school_obj:
            d["school_ru"] = school_obj.name_ru or ""
        if not d.get("district") and school_obj:
            d["district"] = school_obj.district or ""
        if not d.get("region") and school_obj:
            d["region"] = school_obj.region or ""

        if current_user.avatar and not d.get("photo"):
            d["photo"] = current_user.avatar
        if current_user.illness_info and not d.get("story_uz"):
            d["story_uz"] = current_user.illness_info

    product = Product(**d, user_id=current_user.id)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product_to_dict(product, current_user, student)


async def _can_manage_product(db, product, user) -> bool:
    if user.role == "superadmin":
        return True
    if product.user_id == user.id:
        return True
    # Bir maktab adminlari bir-birining mahsulotini boshqarishi mumkin
    if product.student_id and user.school_id:
        s = await db.execute(select(Student).where(Student.id == product.student_id))
        student = s.scalar_one_or_none()
        if student and student.school_id == user.school_id:
            return True
    return False


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

    if not await _can_manage_product(db, product, current_user):
        raise HTTPException(status_code=403, detail="Siz bu mahsulotni boshqara olmaysiz")

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

    if not await _can_manage_product(db, product, current_user):
        raise HTTPException(status_code=403, detail="Siz bu mahsulotni o'chira olmaysiz")

    await product_crud.delete(db, product)
    return {"success": True}


@router.get("/pending/list")
async def get_pending_products(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Maktab admini uchun — Telegram orqali yuklangan, hali tasdiqlanmagan mahsulotlar."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Faqat admin")

    if current_user.role == "superadmin":
        q = select(Product).where(Product.status == "pending")
    elif current_user.school_id:
        sub = select(Student.id).where(Student.school_id == current_user.school_id)
        student_ids = [r[0] for r in (await db.execute(sub)).all()]
        if not student_ids:
            return []
        q = select(Product).where(
            Product.status == "pending",
            Product.student_id.in_(student_ids),
        )
    else:
        return []

    q = q.order_by(Product.id.desc())
    result = await db.execute(q)
    products = result.scalars().all()

    response = []
    for p in products:
        user, student = await _fetch_author_info(db, p)
        response.append(product_to_dict(p, user, student))
    return response


@router.post("/{product_id}/approve")
async def approve_product(
    product_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Faqat admin")

    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    if product.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Mahsulot allaqachon {product.status}"
        )

    # Maktab tekshiruvi (superadmin tashqarisida)
    if current_user.role != "superadmin":
        if not product.student_id:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        s = await db.execute(select(Student).where(Student.id == product.student_id))
        student = s.scalar_one_or_none()
        if not student or student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=403,
                detail="Faqat o'z maktabingiz mahsulotlarini tasdiqlay olasiz",
            )

    product.status = "approved"
    await db.flush()
    await db.refresh(product)
    return {"success": True, "id": product.id, "status": product.status}


@router.post("/{product_id}/reject")
async def reject_product(
    product_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rad etilgan mahsulot bazadan butunlay o'chiriladi (har qanday status'da)."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Faqat admin")

    product = await product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    if current_user.role != "superadmin":
        if not product.student_id:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        s = await db.execute(select(Student).where(Student.id == product.student_id))
        student = s.scalar_one_or_none()
        if not student or student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=403,
                detail="Faqat o'z maktabingiz mahsulotlarini rad eta olasiz",
            )

    deleted_id = product.id
    await db.delete(product)
    await db.flush()
    return {"success": True, "id": deleted_id, "deleted": True}


@router.get("/user/{user_id}")
async def get_products_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Ma'lum user mahsulotlari — muallif sahifasi uchun (faqat tasdiqlangan)"""
    result = await db.execute(
        select(Product)
        .where(Product.user_id == user_id)
        .where(Product.stock > 0)
        .where(Product.status == "approved")
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