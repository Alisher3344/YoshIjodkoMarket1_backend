from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from ..core.database import Base


class School(Base):
    __tablename__ = "schools"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(300), nullable=False)
    name_ru     = Column(String(300), default="")
    district    = Column(String(200), default="")
    region      = Column(String(200), default="Qashqadaryo viloyati")
    address     = Column(String(500), default="")
    phone       = Column(String(50), default="")
    photo       = Column(Text, default="")           # base64 rasm
    description = Column(Text, default="")
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
