from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..core.database import get_db, AsyncSessionLocal
from ..core.security import check_role
from ..crud import order as order_crud
from ..models.order import Order, OrderItem
from ..models.product import Product
from ..schemas.order import OrderCreate, OrderStatusUpdate
from ..utils.telegram import send_telegram

router = APIRouter()


async def notify_order_safe(order_id: int):
    """Background: telegram'ga xabar — xato bo'lsa ham orderga ta'sir qilmaydi"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            if not order:
                print(f"⚠️  Order {order_id} topilmadi")
                return

            lines = [
    "🛒 <b>YANGI BUYURTMA!</b>",
    "",
    f"👤 <b>Mijoz:</b> {order.customer_name}",
    f"📞 <b>Telefon:</b> {order.customer_phone}",
]

# Login qilgan xaridor ma'lumoti
            if order.buyer_user_id:
                lines.append("")
                lines.append("🔐 <b>Tizimdagi foydalanuvchi:</b>")
                lines.append(f"   👤 Ism: {order.buyer_user_name}")
                lines.append(f"   📞 Telefon: <code>{order.buyer_user_phone}</code>")
                lines.append(f"   🆔 User ID: {order.buyer_user_id}")

            if order.customer_address:
                lines.append(f"📍 <b>Manzil:</b> {order.customer_address}")
            if order.city:
                lines.append(f"🏙 <b>Shahar:</b> {order.city}")

            pay_map = {"cash": "💵 Naqd", "click": "💳 Click", "payme": "💳 Payme", "uzum": "💳 Uzum"}
            if order.payment_method:
                lines.append(f"💰 <b>To'lov:</b> {pay_map.get(order.payment_method, order.payment_method)}")

            lines.append("")
            lines.append("📦 <b>Mahsulotlar:</b>")

            for i, item in enumerate(order.items, 1):
                name = item.name_uz or "Noma'lum"
                lines.append("")
                lines.append(f"{i}. <b>{name}</b>")
                lines.append(f"   💵 {item.price:,.0f} so'm × {item.qty}")
                lines.append(f"   💰 Jami: {(item.price * item.qty):,.0f} so'm")
                if item.author:
                    lines.append(f"   👤 Muallif: {item.author}")
                if item.school:
                    lines.append(f"   🏫 Maktab: {item.school}")
                if item.student_type == "disabled" and item.card_number:
                    lines.append(f"   ❤️ <b>Imkoniyati cheklangan</b>")
                    lines.append(f"   💳 Karta: <code>{item.card_number}</code>")

            lines.append("")
            lines.append(f"💰 <b>Jami: {order.total:,.0f} so'm</b>")
            if order.note:
                lines.append(f"📝 <b>Izoh:</b> {order.note}")

            message = "\n".join(lines)

            # Birinchi rasmni topish
            first_image = None
            for item in order.items:
                if item.image:
                    first_image = item.image
                    break

            if first_image and first_image.startswith("data:image"):
                await send_telegram(message, image_base64=first_image)
            else:
                await send_telegram(message)

    except Exception as e:
        print(f"❌ Telegram bildirishnoma xato (orderga ta'sir qilmadi): {e}")


@router.post("/")
async def create_order(
    data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        order = await order_crud.create_order(db, data)
        await db.commit()
        print(f"✅ Order yaratildi: ID={order.id}")

        # Telegram — background (xato bo'lsa ham orderga ta'sir qilmaydi)
        background_tasks.add_task(notify_order_safe, order.id)

        return {"success": True, "id": order.id}
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()  # To'liq xatoni terminalga chiqaradi
        print(f"❌ Order yaratishda xato: {e}")
        raise HTTPException(status_code=500, detail=f"Buyurtma saqlanmadi: {str(e)}")


@router.get("/", dependencies=[Depends(check_role("moderator"))])
async def get_orders(db: AsyncSession = Depends(get_db)):
    return await order_crud.get_all_orders(db)


@router.put("/{order_id}/status", dependencies=[Depends(check_role("moderator"))])
async def update_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    order = await order_crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    await order_crud.update_order_status(db, order, data.status)
    return {"success": True}