from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    name:      str
    username:  str
    password:  str
    phone:     Optional[str] = ""
    school:    Optional[str] = ""
    full_name: Optional[str] = ""
    avatar:    Optional[str] = ""
    role:      Optional[str] = "admin"


class UserUpdate(BaseModel):
    name:      Optional[str] = None
    username:  Optional[str] = None
    phone:     Optional[str] = None
    school:    Optional[str] = None
    full_name: Optional[str] = None
    avatar:    Optional[str] = None
    role:      Optional[str] = None
    password:  Optional[str] = None


class ProfileUpdate(BaseModel):
    name:      Optional[str] = None
    full_name: Optional[str] = None
    phone:     Optional[str] = None
    school:    Optional[str] = None
    avatar:    Optional[str] = None


class UserResponse(BaseModel):
    id:        int
    name:      str
    full_name: str
    username:  str
    phone:     str
    school:    str
    avatar:    str
    role:      str
    active:    bool

    class Config:
        from_attributes = True