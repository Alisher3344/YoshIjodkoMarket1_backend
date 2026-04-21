from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    name:         str
    username:     str
    password:     str
    email:        str   = ""
    phone:        str   = ""
    full_name:    str   = ""
    school:       str   = ""
    age:          int   = 0
    is_disabled:  bool  = False
    card_number:  str   = ""
    illness_info: str   = ""
    avatar:       str   = ""
    role:         str   = "student"


class UserUpdate(BaseModel):
    name:         str
    username:     str
    email:        str   = ""
    phone:        str   = ""
    full_name:    str   = ""
    school:       str   = ""
    age:          int   = 0
    is_disabled:  bool  = False
    card_number:  str   = ""
    illness_info: str   = ""
    avatar:       str   = ""
    role:         str   = "student"
    password:     Optional[str] = None


class UserResponse(BaseModel):
    id:           int
    name:         str
    full_name:    str
    username:     str
    email:        str
    phone:        str
    school:       str
    age:          int
    is_disabled:  bool
    card_number:  str
    illness_info: str
    avatar:       str
    role:         str
    active:       bool

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Foydalanuvchi o'z profilini yangilash uchun"""
    name:         str
    full_name:    str   = ""
    school:       str   = ""
    age:          int   = 0
    card_number:  str   = ""
    illness_info: str   = ""
    avatar:       str   = ""