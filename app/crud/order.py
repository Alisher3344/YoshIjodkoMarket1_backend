from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .. import models
from ..models.order import Order, OrderItem, CustomOrder
from ..models.product import Product


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

    await db.flush()
    await db.refresh(order)
    return order


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