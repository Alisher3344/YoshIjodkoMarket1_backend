from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.security import check_role, require_superadmin
from ..crud import user as user_crud
from ..schemas.user import UserCreate, UserUpdate

router = APIRouter()


@router.get("/", dependencies=[Depends(check_role("admin"))])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await user_crud.get_all(db)


@router.post("/", dependencies=[Depends(require_superadmin)])
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Majburiy maydonlarni tekshirish
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Ism kiritilishi shart")
    if not data.full_name.strip():
        raise HTTPException(status_code=400, detail="To'liq ism-familiya kiritilishi shart")
    if not data.school.strip():
        raise HTTPException(status_code=400, detail="Maktab nomi kiritilishi shart")
    if not data.phone.strip():
        raise HTTPException(status_code=400, detail="Telefon raqami kiritilishi shart")
    if not data.username.strip():
        raise HTTPException(status_code=400, detail="Username kiritilishi shart")
    if not data.password or len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Parol kamida 4 ta belgi bo'lsin")

    if await user_crud.get_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Bu username band")

    return await user_crud.create(db, data)


@router.put("/{user_id}", dependencies=[Depends(require_superadmin)])
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return await user_crud.update(db, user, data)


@router.delete("/{user_id}", dependencies=[Depends(require_superadmin)])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    await user_crud.delete(db, user)
    return {"success": True}


@router.patch("/{user_id}/toggle", dependencies=[Depends(require_superadmin)])
async def toggle_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    updated = await user_crud.toggle_active(db, user)
    return {"success": True, "active": updated.active}