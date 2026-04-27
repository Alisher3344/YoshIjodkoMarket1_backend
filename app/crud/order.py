from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .. import models
from ..models.order import Order, OrderItem, CustomOrder
from ..models.product import Product
from ..models.student import Student
from ..models.user import User
from ..utils.telegram import send_telegram_dm


async def create_order(db, data):
    order = Order(
        customer_name    = data.customer_name,
        customer_phone   = data.customer_phone,
        customer_address = data.customer_address,
        city             = data.city,
        payment_method   = data.payment_method,
        note             = data.note,
        total            = data.total,
        buyer_user_id    = data.buyer_user_id,
        buyer_user_name  = data.buyer_user_name,
        buyer_user_phone = data.buyer_user_phone,
    )
    db.add(order)
    await db.flush()

    # Stock 0 ga tushgan student-mahsulotlarini kuzatish — keyin Telegram notify
    sold_out = []  # [{product, qty}]

    for item in data.items:
        # OrderItem yaratish
        order_item = OrderItem(
            order_id     = order.id,
            product_id   = item.product_id,
            name_uz      = item.name_uz,
            name_ru      = item.name_ru,
            price        = item.price,
            qty          = item.qty,
            image        = item.image,
            author       = item.author,
            school       = item.school,
            card_number  = item.card_number,
            student_type = item.student_type,
        )
        db.add(order_item)

        # Mahsulot stock'ini kamaytirish va sold ni oshirish
        if item.product_id:
            prod_res = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = prod_res.scalar_one_or_none()
            if product:
                product.stock = max(0, (product.stock or 0) - item.qty)
                product.sold  = (product.sold or 0) + item.qty

                # Stock 0 va student'ga bog'langan bo'lsa — notify ro'yxatiga qo'shamiz
                if product.stock == 0 and product.student_id:
                    sold_out.append({"product": product, "qty": item.qty})

    await db.flush()
    await db.refresh(order)

    # Notifikatsiyalarni yuborish (xato bo'lsa ham order yaratiladi)
    for entry in sold_out:
        try:
            await _notify_student_sold_out(
                db,
                product=entry["product"],
                qty=entry["qty"],
                buyer_name=data.customer_name or "",
                buyer_phone=data.customer_phone or "",
            )
        except Exception as e:
            print(f"[Telegram notify] xato: {e}")

    return order


async def _notify_student_sold_out(
    db, *, product, qty: int, buyer_name: str, buyer_phone: str
):
    """Student stock=0 bo'lganda Telegram orqali xabar yuborish.
    Faqat student Telegram orqali ro'yxatdan o'tgan bo'lsa (user.telegram_id mavjud).
    """
    if not product or not product.student_id:
        return

    s_res = await db.execute(select(Student).where(Student.id == product.student_id))
    student = s_res.scalar_one_or_none()
    if not student or not student.user_id:
        return

    u_res = await db.execute(select(User).where(User.id == student.user_id))
    user = u_res.scalar_one_or_none()
    if not user or not user.telegram_id:
        return

    text = (
        f"🎉 <b>Tabriklaymiz! Mahsulotingiz sotildi</b>\n\n"
        f"📦 <b>Mahsulot:</b> {product.name_uz}\n"
        f"🛒 <b>Holat:</b> Stock tugadi (0 dona qoldi)\n"
        f"💰 <b>Narxi:</b> {int(product.price or 0):,} so'm\n\n"
        f"👤 <b>Xaridor:</b> {buyer_name or '—'}\n"
        f"📞 <b>Telefon:</b> {buyer_phone or '—'}\n"
        f"🔢 <b>Sotilgan soni:</b> {qty} dona\n\n"
        f"💡 Yangi mahsulot yuklash uchun Mini App'ni oching."
    ).replace(",", " ")

    await send_telegram_dm(int(user.telegram_id), text)


async def get_all_orders(db):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def get_order_by_id(db, order_id):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def update_order_status(db, order, status):
    order.status = status
    await db.flush()
    return order


async def create_custom_order(db, data):
    custom_order = CustomOrder(**data.model_dump())
    db.add(custom_order)
    await db.flush()
    await db.refresh(custom_order)
    return custom_order


async def get_all_custom_orders(db):
    result = await db.execute(
        select(CustomOrder).order_by(CustomOrder.created_at.desc())
    )
    return result.scalars().all()


async def get_custom_order_by_id(db, order_id):
    result = await db.execute(
        select(CustomOrder).where(CustomOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def update_custom_order_status(db, order, status):
    order.status = status
    await db.flush()
    return order