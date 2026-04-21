from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.security import check_role
from ..crud import order as order_crud
from ..schemas.order import CustomOrderCreate, CustomOrderStatusUpdate

router = APIRouter()


@router.post("/")
async def create_custom_order(data: CustomOrderCreate, db: AsyncSession = Depends(get_db)):
    order = await order_crud.create_custom_order(db, data)
    return {"success": True, "id": order.id}


@router.get("/", dependencies=[Depends(check_role("moderator"))])
async def get_custom_orders(db: AsyncSession = Depends(get_db)):
    return await order_crud.get_all_custom_orders(db)


@router.put("/{order_id}/status", dependencies=[Depends(check_role("moderator"))])
async def update_status(
    order_id: int,
    data: CustomOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    order = await order_crud.get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    await order_crud.update_custom_order_status(db, order, data.status)
    return {"success": True}