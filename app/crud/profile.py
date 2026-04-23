from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.profile import Profile
from ..schemas.profile import ProfileCreate, ProfileUpdate


async def get_all(db: AsyncSession):
    """Hamma profillar (saytda ko'rsatish uchun)"""
    result = await db.execute(
        select(Profile).where(Profile.active == True).order_by(Profile.id.desc())
    )
    return result.scalars().all()


async def get_by_owner(db: AsyncSession, owner_id: int):
    """Admin o'z profillari ro'yxati"""
    result = await db.execute(
        select(Profile).where(Profile.owner_id == owner_id).order_by(Profile.id.desc())
    )
    return result.scalars().all()


async def get_by_id(db: AsyncSession, profile_id: int):
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, owner_id: int, data: ProfileCreate) -> Profile:
    profile = Profile(
        owner_id     = owner_id,
        name         = data.name,
        name_ru      = data.name_ru,
        full_name    = data.full_name,
        bio_uz       = data.bio_uz,
        bio_ru       = data.bio_ru,
        phone        = data.phone,
        school       = data.school,
        school_ru    = data.school_ru,
        district     = data.district,
        district_ru  = data.district_ru,
        region       = data.region,
        region_ru    = data.region_ru,
        age          = data.age,
        grade        = data.grade,
        is_disabled  = data.is_disabled,
        card_number  = data.card_number,
        illness_info = data.illness_info,
        avatar       = data.avatar,
        active       = True,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update(db: AsyncSession, profile: Profile, data: ProfileUpdate) -> Profile:
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def delete(db: AsyncSession, profile: Profile):
    await db.delete(profile)
    await db.flush()


async def toggle_active(db: AsyncSession, profile: Profile) -> Profile:
    profile.active = not profile.active
    await db.flush()
    await db.refresh(profile)
    return profile