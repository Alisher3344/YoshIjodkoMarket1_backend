from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from ..core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(200), nullable=False, unique=True, index=True)
    country    = Column(String(100), default="O'zbekiston", index=True)
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class District(Base):
    """Shahar yoki tuman — ikkalasi ham region ostida saqlanadi."""

    __tablename__ = "districts"

    id         = Column(Integer, primary_key=True, index=True)
    region_id  = Column(
        Integer, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name       = Column(String(200), nullable=False, index=True)
    type       = Column(String(20), default="district", index=True)  # 'city' yoki 'district'
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
