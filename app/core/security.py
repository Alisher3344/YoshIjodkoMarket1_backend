from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .config import settings
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    from ..models.user import User
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token noto'g'ri")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token muddati o'tgan")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
    if not user.active:
        raise HTTPException(status_code=403, detail="Hisob bloklangan")
    return user


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Faqat admin")
    return current_user


ROLE_HIERARCHY = {
    "superadmin": 4,
    "admin":      3,
    "moderator":  2,
    "viewer":     1,
}


def check_role(required_role: str):
    async def checker(current_user=Depends(get_current_user)):
        if ROLE_HIERARCHY.get(current_user.role, 0) < ROLE_HIERARCHY.get(required_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"Ruxsat yo'q — kamida '{required_role}' roli kerak"
            )
        return current_user
    return checker


async def require_superadmin(current_user=Depends(get_current_user)):
    if ROLE_HIERARCHY.get(current_user.role, 0) < 4:
        raise HTTPException(status_code=403, detail="Faqat superadmin")
    return current_user