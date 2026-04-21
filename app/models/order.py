from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id                = Column(Integer, primary_key=True, index=True)
    customer_name     = Column(String(200), nullable=False)
    customer_phone    = Column(String(50),  nullable=False)
    customer_address  = Column(Text,        default="")
    city              = Column(String(100), default="")
    payment_method    = Column(String(50),  default="cash")
    note              = Column(Text,        default="")
    total             = Column(Float,       default=0.0)
    status            = Column(String(50),  default="new")

    # Login qilgan xaridor (ixtiyoriy)
    buyer_user_id     = Column(Integer,     default=None, nullable=True)
    buyer_user_name   = Column(String(200), default="")
    buyer_user_phone  = Column(String(50),  default="")

    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    items             = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id            = Column(Integer, primary_key=True, index=True)
    order_id      = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id    = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    name_uz       = Column(String(500), default="")
    name_ru       = Column(String(500), default="")
    price         = Column(Float,   default=0.0)
    qty           = Column(Integer, default=1)
    image         = Column(Text,    default="")
    author        = Column(String(300), default="")
    school        = Column(String(300), default="")
    card_number   = Column(String(50),  default="")
    student_type  = Column(String(50),  default="normal")

    order         = relationship("Order", back_populates="items")


class CustomOrder(Base):
    __tablename__ = "custom_orders"

    id                = Column(Integer, primary_key=True, index=True)
    customer_name     = Column(String(200), nullable=False)
    customer_phone    = Column(String(50),  nullable=False)
    customer_address  = Column(Text,         default="")
    order_type        = Column(String(200), default="")
    description       = Column(Text,         default="")
    budget            = Column(String(100), default="")
    deadline          = Column(String(100), default="")
    payment_method    = Column(String(50),  default="cash")
    status            = Column(String(50),  default="new")
    created_at        = Column(DateTime(timezone=True), server_default=func.now())