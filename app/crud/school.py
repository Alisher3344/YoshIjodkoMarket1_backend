from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.school import School
from ..models.user import User
from ..schemas.school import SchoolCreate, SchoolUpdate


async def get_all(db: AsyncSession):
    result = await db.execute(select(School).order_by(School.id.desc()))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, school_id: int):
    result = await db.execute(select(School).where(School.id == school_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: SchoolCreate) -> School:
    school = School(**data.model_dump(), active=True)
    db.add(school)
    await db.flush()
    await db.refresh(school)
    return school


async def update(db: AsyncSession, school: School, data: SchoolUpdate) -> School:
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        if value is not None:
            setattr(school, key, value)
    await db.flush()
    await db.refresh(school)
    return school


async def delete(db: AsyncSession, school: School):
    await db.delete(school)
    await db.flush()


async def admins_of_school(db: AsyncSession, school_id: int):
    """Maktabga biriktirilgan adminlar ro'yxati"""
    result = await db.execute(
        select(User)
        .where(User.school_id == school_id, User.role.in_(["admin", "superadmin"]))
        .order_by(User.id.desc())
    )
    return result.scalars().all()


async def admin_count(db: AsyncSession, school_id: int) -> int:
    result = await db.execute(
        select(func.count(User.id)).where(
            User.school_id == school_id, User.role.in_(["admin", "superadmin"])
        )
    )
    return int(result.scalar() or 0)
