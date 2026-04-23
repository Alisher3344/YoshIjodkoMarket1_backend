from typing import Optional
from pydantic import BaseModel


class ProfileBase(BaseModel):
    name:         str
    name_ru:      str = ""
    full_name:    str = ""
    bio_uz:       str = ""
    bio_ru:       str = ""
    phone:        str = ""
    school:       str = ""
    school_ru:    str = ""
    district:     str = ""
    district_ru:  str = ""
    region:       str = ""
    region_ru:    str = ""
    age:          int = 0
    grade:        str = ""
    is_disabled:  bool = False
    card_number:  str = ""
    illness_info: str = ""
    avatar:       str = ""


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id:         int
    owner_id:   int
    active:     bool

    class Config:
        from_attributes = True  