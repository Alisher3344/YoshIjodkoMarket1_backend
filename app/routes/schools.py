from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import require_superadmin, get_current_user, hash_password
from ..crud import school as school_crud
from ..models.user import User
from ..schemas.school import SchoolCreate, SchoolUpdate

router = APIRouter()


def school_dict(s) -> dict:
    return {
        "id":          s.id,
        "name":        s.name,
        "name_ru":     s.name_ru or "",
        "district":    s.district or "",
        "region":      s.region or "",
        "address":     s.address or "",
        "phone":       s.phone or "",
        "photo":       s.photo or "",
        "description": s.description or "",
        "active":      s.active,
    }


def admin_dict(u: User) -> dict:
    return {
        "id":        u.id,
        "name":      u.name or "",
        "full_name": u.full_name or "",
        "username":  u.username,
        "phone":     u.phone or "",
        "role":      u.role,
        "active":    u.active,
        "school_id": u.school_id,
    }


@router.get("/")
async def list_schools(db: AsyncSession = Depends(get_db)):
    schools = await school_crud.get_all(db)
    out = []
    for s in schools:
        d = school_dict(s)
        d["admin_count"] = await school_crud.admin_count(db, s.id)
        out.append(d)
    return out


@router.get("/{school_id}")
async def get_school(school_id: int, db: AsyncSession = Depends(get_db)):
    s = await school_crud.get_by_id(db, school_id)
    if not s:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")
    return school_dict(s)


@router.get("/{school_id}/admins")
async def school_admins(
    school_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
    admins = await school_crud.admins_of_school(db, school_id)
    return [admin_dict(a) for a in admins]


@router.post("/", dependencies=[Depends(require_superadmin)])
async def create_school(data: SchoolCreate, db: AsyncSession = Depends(get_db)):
    school = await school_crud.create(db, data)
    return school_dict(school)


@router.put("/{school_id}", dependencies=[Depends(require_superadmin)])
async def update_school(
    school_id: int, data: SchoolUpdate, db: AsyncSession = Depends(get_db)
):
    s = await school_crud.get_by_id(db, school_id)
    if not s:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")
    s = await school_crud.update(db, s, data)
    return school_dict(s)


@router.delete("/{school_id}", dependencies=[Depends(require_superadmin)])
async def delete_school(school_id: int, db: AsyncSession = Depends(get_db)):
    s = await school_crud.get_by_id(db, school_id)
    if not s:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")
    await school_crud.delete(db, s)
    return {"success": True}


# ─── Admin biriktirish: yangi admin yaratib, maktabga bog'lash ───
class AssignAdminPayload(SchoolUpdate):  # dummy parent so reuses BaseModel
    pass


@router.post("/{school_id}/admins", dependencies=[Depends(require_superadmin)])
async def assign_new_admin(
    school_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Yangi admin yaratib, maktabga biriktiradi.
    payload: {name, full_name, phone, username, password}
    Username — majburiy, qo'lda kiritiladi (telefondan farqli bo'lishi mumkin).
    """
    school = await school_crud.get_by_id(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")

    name = (payload.get("name") or "").strip()
    full_name = (payload.get("full_name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not name:
        raise HTTPException(status_code=400, detail="Ism kiritilishi shart")
    if not username:
        raise HTTPException(status_code=400, detail="Username kiritilishi shart")
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak",
        )

    from sqlalchemy import select

    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Bu username allaqachon mavjud"
        )

    new_admin = User(
        name=name,
        full_name=full_name,
        username=username,
        phone=phone,
        password=hash_password(password),
        role="admin",
        active=True,
        school=school.name,
        school_id=school.id,
    )
    db.add(new_admin)
    await db.flush()
    await db.refresh(new_admin)
    return admin_dict(new_admin)


@router.delete(
    "/{school_id}/admins/{admin_id}",
    dependencies=[Depends(require_superadmin)],
)
async def detach_admin(
    school_id: int, admin_id: int, db: AsyncSession = Depends(get_db)
):
    """Adminni maktabdan ajratish (admin saqlanadi, faqat school_id null bo'ladi)"""
    from sqlalchemy import select

    res = await db.execute(select(User).where(User.id == admin_id))
    admin = res.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin topilmadi")
    if admin.school_id != school_id:
        raise HTTPException(status_code=400, detail="Admin bu maktabga biriktirilmagan")
    admin.school_id = None
    admin.school = ""
    await db.flush()
    return {"success": True}
