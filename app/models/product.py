from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Product(Base):
    __tablename__ = "products"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    student_id   = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True)
    name_uz      = Column(String, nullable=False)
    name_ru      = Column(String, default="")
    desc_uz      = Column(Text,   default="")
    desc_ru      = Column(Text,   default="")
    price        = Column(Float, nullable=False)
    old_price    = Column(Float, nullable=True)
    stock        = Column(Integer, default=1)
    category     = Column(String, default="")
    badge        = Column(String, default="")
    author       = Column(String, default="")
    author_ru    = Column(String, default="")
    school       = Column(String, default="")
    school_ru    = Column(String, default="")
    grade        = Column(String, default="")
    district     = Column(String, default="")
    district_ru  = Column(String, default="")
    region       = Column(String, default="")
    region_ru    = Column(String, default="")
    phone        = Column(String, default="")
    student_type = Column(String, default="normal")
    card_number  = Column(String, default="")
    story_uz     = Column(Text,   default="")
    story_ru     = Column(Text,   default="")
    photo        = Column(String, default="")
    image        = Column(String, default="")
    rating       = Column(Float,  default=5.0)
    reviews      = Column(Integer, default=0)
    sold         = Column(Integer, default=0)
    status       = Column(String(20), default="approved", nullable=False, index=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())