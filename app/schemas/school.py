from typing import Optional
from pydantic import BaseModel


class SchoolBase(BaseModel):
    name:        str
    name_ru:     Optional[str] = ""
    district:    Optional[str] = ""
    region:      Optional[str] = "Qashqadaryo viloyati"
    address:     Optional[str] = ""
    phone:       Optional[str] = ""
    photo:       Optional[str] = ""
    description: Optional[str] = ""


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name:        Optional[str] = None
    name_ru:     Optional[str] = None
    district:    Optional[str] = None
    region:      Optional[str] = None
    address:     Optional[str] = None
    phone:       Optional[str] = None
    photo:       Optional[str] = None
    description: Optional[str] = None


class SchoolResponse(SchoolBase):
    id:     int
    active: bool

    class Config:
        from_attributes = True
