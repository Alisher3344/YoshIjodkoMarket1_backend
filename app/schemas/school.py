from typing import Optional
from pydantic import BaseModel


class SchoolBase(BaseModel):
    name:        str
    name_ru:     Optional[str] = ""
    country:     Optional[str] = "O'zbekiston"
    region:      Optional[str] = "Qashqadaryo viloyati"
    city:        Optional[str] = ""
    district:    Optional[str] = ""
    address:     Optional[str] = ""
    phone:       Optional[str] = ""
    photo:       Optional[str] = ""
    description: Optional[str] = ""


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name:        Optional[str] = None
    name_ru:     Optional[str] = None
    country:     Optional[str] = None
    region:      Optional[str] = None
    city:        Optional[str] = None
    district:    Optional[str] = None
    address:     Optional[str] = None
    phone:       Optional[str] = None
    photo:       Optional[str] = None
    description: Optional[str] = None


class SchoolResponse(SchoolBase):
    id:     int
    active: bool

    class Config:
        from_attributes = True
