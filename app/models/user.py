from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(200), nullable=False)
    full_name     = Column(String(300), default="")       # to'liq ism familiya
    username      = Column(String(100), unique=True, index=True, nullable=False)
    password      = Column(String(200), nullable=False)
    email         = Column(String(200), default="")
    phone         = Column(String(50),  default="")
    school        = Column(String(300), default="")
    age           = Column(Integer,     default=0)
    is_disabled   = Column(Boolean,     default=False)
    card_number   = Column(String(50),  default="")
    illness_info  = Column(Text,        default="")       # kasallik haqida ma'lumot
    avatar        = Column(Text,        default="")       # base64 rasm
    role          = Column(String(50),  default="student")
    active        = Column(Boolean,     default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())