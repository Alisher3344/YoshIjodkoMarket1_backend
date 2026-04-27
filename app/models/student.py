from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, index=True)
    admin_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    status        = Column(String(20), default="approved", nullable=False, index=True)
    school_id     = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    name          = Column(String(200), nullable=False)
    full_name     = Column(String(300), default="")
    name_ru       = Column(String(200), default="")
    avatar        = Column(Text, default="")
    age           = Column(Integer, default=0)
    grade         = Column(String(50), default="")
    school        = Column(String(300), default="")
    school_ru     = Column(String(300), default="")
    district      = Column(String(200), default="")
    district_ru   = Column(String(200), default="")
    region        = Column(String(200), default="")
    region_ru     = Column(String(200), default="")
    phone         = Column(String(50), default="")
    card_number   = Column(String(50), default="")
    is_disabled   = Column(Boolean, default=False)
    illness_info  = Column(Text, default="")
    bio_uz        = Column(Text, default="")
    bio_ru        = Column(Text, default="")
    active        = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())