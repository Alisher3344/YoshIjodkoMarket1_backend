from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.student import Student
from ..schemas.student import StudentCreate, StudentUpdate


async def get_all(db: AsyncSession):
    """Hamma o'quvchilar (sayt mehmonlari uchun) — faqat tasdiqlangan"""
    result = await db.execute(
        select(Student)
        .where(Student.active == True, Student.status == "approved")
        .order_by(Student.id.desc())
    )
    return result.scalars().all()


async def get_by_admin(db: AsyncSession, admin_id: int):
    """Admin o'zi yaratgan o'quvchilari (legacy fallback) — faqat tasdiqlangan"""
    result = await db.execute(
        select(Student)
        .where(Student.admin_id == admin_id, Student.status == "approved")
        .order_by(Student.id.desc())
    )
    return result.scalars().all()


async def get_by_school(db: AsyncSession, school_id: int):
    """Maktabga tegishli tasdiqlangan o'quvchilar"""
    result = await db.execute(
        select(Student)
        .where(Student.school_id == school_id, Student.status == "approved")
        .order_by(Student.id.desc())
    )
    return result.scalars().all()


async def get_pending_by_school(db: AsyncSession, school_id: int):
    """Maktab adminlari uchun: status='pending' bo'lgan ariza yuborgan o'quvchilar"""
    result = await db.execute(
        select(Student)
        .where(Student.school_id == school_id, Student.status == "pending")
        .order_by(Student.id.desc())
    )
    return result.scalars().all()


async def get_by_user(db: AsyncSession, user_id: int):
    """Telegram foydalanuvchisining student qaydi (bo'lsa)"""
    result = await db.execute(
        select(Student).where(Student.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def approve(db: AsyncSession, student: Student, admin_id: int) -> Student:
    student.status = "approved"
    student.admin_id = admin_id
    student.active = True
    await db.flush()
    await db.refresh(student)
    return student


async def reject(db: AsyncSession, student: Student) -> Student:
    student.status = "rejected"
    student.active = False
    await db.flush()
    await db.refresh(student)
    return student


async def get_by_id(db: AsyncSession, student_id: int):
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    admin_id: int,
    data: StudentCreate,
    school_id: int = None,
) -> Student:
    payload = data.model_dump()
    # schemada school_id bo'lsa ham, parent override qiladi
    if school_id is not None:
        payload["school_id"] = school_id
    elif "school_id" not in payload:
        payload["school_id"] = None
    student = Student(admin_id=admin_id, **payload, active=True)
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


async def update(db: AsyncSession, student: Student, data: StudentUpdate) -> Student:
    for key, value in data.model_dump().items():
        setattr(student, key, value)
    await db.flush()
    await db.refresh(student)
    return student


async def delete(db: AsyncSession, student: Student):
    await db.delete(student)
    await db.flush()


async def toggle_active(db: AsyncSession, student: Student) -> Student:
    student.active = not student.active
    await db.flush()
    await db.refresh(student)
    return student