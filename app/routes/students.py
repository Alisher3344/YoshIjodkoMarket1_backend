from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import get_current_user, require_admin, require_superadmin
from ..crud import student as student_crud
from ..schemas.student import StudentCreate, StudentUpdate
from ..models.product import Product
from ..models.student import Student
from ..models.school import School
from ..models.user import User

router = APIRouter()


def _can_manage(student: Student, user) -> bool:
    """Foydalanuvchi shu o'quvchini boshqara oladimi?
    - SuperAdmin har doim ha
    - O'quvchini yaratgan admin (admin_id mos kelsa) — ha
    - Bir maktabga biriktirilgan boshqa adminlar ham — ha (school_id mos kelsa)
    """
    if user.role == "superadmin":
        return True
    if student.admin_id == user.id:
        return True
    if (
        student.school_id is not None
        and user.school_id is not None
        and student.school_id == user.school_id
    ):
        return True
    return False


@router.get("/")
async def list_students(db: AsyncSession = Depends(get_db)):
    return await student_crud.get_all(db)


@router.get("/all-grouped", dependencies=[Depends(require_superadmin)])
async def all_students_grouped_by_school(
    db: AsyncSession = Depends(get_db),
):
    """Superadmin uchun — barcha o'quvchilar (admin yaratgan + Telegram'dan kelganlar)
    maktablar bo'yicha guruhlangan. Status filter yo'q — barcha holatdagi (rejected dan tashqari)
    o'quvchilarni ko'rsatadi."""
    schools_res = await db.execute(select(School).order_by(School.name))
    schools = schools_res.scalars().all()

    students_res = await db.execute(
        select(Student).order_by(Student.id.desc())
    )
    students = students_res.scalars().all()

    user_ids = set()
    for s in students:
        if s.user_id:
            user_ids.add(s.user_id)
    users_map = {}
    if user_ids:
        u_res = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in u_res.scalars().all():
            users_map[u.id] = u

    by_school: dict = {}
    no_school: list = []
    for student in students:
        if student.status == "rejected":
            continue
        u = users_map.get(student.user_id) if student.user_id else None
        item = {
            "id":         student.id,
            "name":       student.name or "",
            "full_name":  student.full_name or "",
            "grade":      student.grade or "",
            "avatar":     student.avatar or "",
            "phone":      student.phone or "",
            "telegram_username": (u.telegram_username if u else "") or "",
            "telegram_id": u.telegram_id if u else None,
            "status":     student.status or "approved",
            "source":     "telegram" if student.user_id else "admin",
        }
        if student.school_id:
            by_school.setdefault(student.school_id, []).append(item)
        else:
            no_school.append(item)

    out = []
    for s in schools:
        out.append({
            "school_id":   s.id,
            "school_name": s.name,
            "country":     s.country or "O'zbekiston",
            "region":      s.region or "",
            "city":        s.city or "",
            "district":    s.district or "",
            "students":    by_school.get(s.id, []),
        })
    if no_school:
        out.append({
            "school_id":   None,
            "school_name": "Maktabsiz",
            "country":     "",
            "region":      "",
            "city":        "",
            "district":    "",
            "students":    no_school,
        })
    return out


@router.get("/{student_id}")
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return student


@router.get("/{student_id}/products")
async def student_products(student_id: int, db: AsyncSession = Depends(get_db)):
    """Faqat tasdiqlangan mahsulotlar — pending va rejected'lar pastki ro'yxatda ko'rinmaydi.
    Pending'lar admin panelda alohida sariq blokda chiqadi (pendingProducts state)."""
    result = await db.execute(
        select(Product)
        .where(Product.student_id == student_id, Product.status == "approved")
        .order_by(Product.id.desc())
    )
    return result.scalars().all()


@router.get("/my/list")
async def my_students(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Agar admin maktabga biriktirilgan bo'lsa — shu maktabning hamma o'quvchilarini qaytaradi.
    Aks holda — faqat o'zi yaratgan o'quvchilarini (eski adminlar uchun).
    Faqat status='approved' o'quvchilar."""
    if current_user.school_id:
        return await student_crud.get_by_school(db, current_user.school_id)
    return await student_crud.get_by_admin(db, current_user.id)


@router.get("/pending/list")
async def pending_students(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Maktab admini uchun — Telegram orqali ariza yuborgan, hali tasdiqlanmagan o'quvchilar."""
    if not current_user.school_id:
        return []
    return await student_crud.get_pending_by_school(db, current_user.school_id)


@router.delete("/admin/{student_id}", dependencies=[Depends(require_superadmin)])
async def superadmin_delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Superadmin har qanday o'quvchini bazadan butunlay o'chiradi."""
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    await student_crud.delete(db, student)
    return {"success": True, "id": student_id, "deleted": True}


@router.post("/{student_id}/approve")
async def approve_student(
    student_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    if student.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"O'quvchi allaqachon {student.status}",
        )
    if (
        current_user.role != "superadmin"
        and student.school_id != current_user.school_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Faqat o'z maktabingizning arizalarini tasdiqlay olasiz",
        )
    updated = await student_crud.approve(db, student, admin_id=current_user.id)
    return {"success": True, "student": {
        "id": updated.id,
        "name": updated.name,
        "status": updated.status,
    }}


@router.post("/{student_id}/reject")
async def reject_student(
    student_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    if student.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"O'quvchi allaqachon {student.status}",
        )
    if (
        current_user.role != "superadmin"
        and student.school_id != current_user.school_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Faqat o'z maktabingizning arizalarini rad etishingiz mumkin",
        )
    updated = await student_crud.reject(db, student)
    return {"success": True, "student": {
        "id": updated.id,
        "status": updated.status,
    }}


@router.post("/")
async def create_student(
    data: StudentCreate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """O'quvchi yaratilganda avtomatik shu adminning maktabiga bog'lanadi."""
    return await student_crud.create(
        db,
        admin_id=current_user.id,
        data=data,
        school_id=current_user.school_id,
    )


@router.put("/{student_id}")
async def update_student(
    student_id: int,
    data: StudentUpdate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    if not _can_manage(student, current_user):
        raise HTTPException(
            status_code=403,
            detail="Faqat o'z maktabingizning o'quvchilarini tahrirlashingiz mumkin",
        )

    return await student_crud.update(db, student, data)


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    if not _can_manage(student, current_user):
        raise HTTPException(
            status_code=403,
            detail="Faqat o'z maktabingizning o'quvchilarini o'chirishingiz mumkin",
        )

    await student_crud.delete(db, student)
    return {"success": True}


@router.patch("/{student_id}/toggle")
async def toggle_student(
    student_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_crud.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    if not _can_manage(student, current_user):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    updated = await student_crud.toggle_active(db, student)
    return {"success": True, "active": updated.active}
