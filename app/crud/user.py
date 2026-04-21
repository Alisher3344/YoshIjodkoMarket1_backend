from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import hash_password, verify_password


async def get_all(db: AsyncSession):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def check_login(db: AsyncSession, username: str, password: str):
    user = await get_by_username(db, username)
    if not user or not verify_password(password, user.password):
        return None
    return user


async def create(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        name     = data.name,
        username = data.username,
        password = hash_password(data.password),
        email    = data.email,
        role     = data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, data: UserUpdate) -> User:
    user.name     = data.name
    user.username = data.username
    user.email    = data.email
    user.role     = data.role
    if data.password:
        user.password = hash_password(data.password)
    await db.flush()
    await db.refresh(user)
    return user


async def delete(db: AsyncSession, user: User):
    await db.delete(user)
    await db.flush()


async def toggle_active(db: AsyncSession, user: User) -> User:
    user.active = not user.active
    await db.flush()
    await db.refresh(user)
    return user