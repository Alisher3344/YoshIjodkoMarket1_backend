from typing import Optional
from pydantic import BaseModel


class OrderItem(BaseModel):
    product_id:   Optional[int] = None
    name_uz:      str   = ""
    name_ru:      str   = ""
    price:        float = 0.0
    qty:          int   = 1
    image:        str   = ""
    author:       str   = ""
    school:       str   = ""
    card_number:  str   = ""
    student_type: str   = "normal"


class OrderCreate(BaseModel):
    customer_name:     str
    customer_phone:    str
    customer_address:  str   = ""
    city:              str   = ""
    payment_method:    str   = "cash"
    note:              str   = ""
    total:             float = 0.0

    buyer_user_id:     Optional[int] = None
    buyer_user_name:   str   = ""
    buyer_user_phone:  str   = ""

    items: list[OrderItem] = []


class OrderStatusUpdate(BaseModel):
    status: str


class CustomOrderCreate(BaseModel):
    customer_name:    str
    customer_phone:   str
    customer_address: str = ""
    order_type:       str = ""
    description:      str = ""
    budget:           str = ""
    deadline:         str = ""
    payment_method:   str = "cash"


class CustomOrderStatusUpdate(BaseModel):
    status: str