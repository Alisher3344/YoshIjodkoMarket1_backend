"""Hududlar (regions + districts) — DB'dan o'qiladi.
Frontend kaskadli dropdownlar uchun ishlatadi."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import require_superadmin
from ..models.region import Region, District

router = APIRouter()


def region_dict(r: Region, districts=None) -> dict:
    d = {
        "id":      r.id,
        "name":    r.name,
        "country": r.country or "O'zbekiston",
        "active":  r.active,
    }
    if districts is not None:
        d["cities"] = [
            {"id": x.id, "name": x.name}
            for x in districts if x.type == "city" and x.active
        ]
        d["districts"] = [
            {"id": x.id, "name": x.name}
            for x in districts if x.type == "district" and x.active
        ]
    return d


@router.get("/")
async def list_regions(db: AsyncSession = Depends(get_db)):
    """Barcha viloyatlar — har birida shaharlar va tumanlar bilan."""
    res = await db.execute(
        select(Region).where(Region.active == True).order_by(Region.name)
    )
    regions = res.scalars().all()

    # Bitta query bilan barcha districtlarni olamiz
    d_res = await db.execute(
        select(District).where(District.active == True).order_by(District.name)
    )
    all_districts = d_res.scalars().all()
    by_region: dict = {}
    for d in all_districts:
        by_region.setdefault(d.region_id, []).append(d)

    return [region_dict(r, by_region.get(r.id, [])) for r in regions]


@router.get("/{region_id}/districts")
async def region_districts(region_id: int, db: AsyncSession = Depends(get_db)):
    """Bitta viloyatning shaharlari + tumanlari."""
    r_res = await db.execute(select(Region).where(Region.id == region_id))
    region = r_res.scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="Viloyat topilmadi")

    d_res = await db.execute(
        select(District)
        .where(District.region_id == region_id, District.active == True)
        .order_by(District.name)
    )
    districts = d_res.scalars().all()
    return region_dict(region, districts)


# ─── Superadmin uchun CRUD ──────────────────────────────────────────────

@router.post("/", dependencies=[Depends(require_superadmin)])
async def create_region(payload: dict, db: AsyncSession = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nom kiritilishi shart")
    ex = await db.execute(select(Region).where(Region.name == name))
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu nomli viloyat mavjud")
    region = Region(
        name=name,
        country=payload.get("country") or "O'zbekiston",
        active=True,
    )
    db.add(region)
    await db.flush()
    await db.refresh(region)
    return region_dict(region, [])


@router.delete("/{region_id}", dependencies=[Depends(require_superadmin)])
async def delete_region(region_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Region).where(Region.id == region_id))
    region = res.scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="Viloyat topilmadi")
    await db.delete(region)
    return {"success": True}


@router.post("/{region_id}/districts", dependencies=[Depends(require_superadmin)])
async def create_district(
    region_id: int, payload: dict, db: AsyncSession = Depends(get_db)
):
    name = (payload.get("name") or "").strip()
    dtype = payload.get("type") or "district"
    if dtype not in ("city", "district"):
        raise HTTPException(status_code=400, detail="type 'city' yoki 'district' bo'lishi kerak")
    if not name:
        raise HTTPException(status_code=400, detail="Nom kiritilishi shart")

    r_res = await db.execute(select(Region).where(Region.id == region_id))
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Viloyat topilmadi")

    d = District(region_id=region_id, name=name, type=dtype, active=True)
    db.add(d)
    await db.flush()
    await db.refresh(d)
    return {"id": d.id, "name": d.name, "type": d.type, "region_id": d.region_id}


@router.delete(
    "/{region_id}/districts/{district_id}",
    dependencies=[Depends(require_superadmin)],
)
async def delete_district(
    region_id: int, district_id: int, db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(District).where(
            District.id == district_id, District.region_id == region_id
        )
    )
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Tuman topilmadi")
    await db.delete(d)
    return {"success": True}
