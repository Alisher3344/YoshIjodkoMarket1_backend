from typing import Optional
from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    # extra fieldlarni e'tiborsiz qoldiradi (frontend qo'shimcha yubarsa xato bermaydi)
    model_config = ConfigDict(extra="ignore")

    name:         str
    full_name:    str = ""
    name_ru:      str = ""
    avatar:       str = ""
    age:          int = 0
    grade:        str = ""
    school:       str = ""
    school_ru:    str = ""
    district:     str = ""
    district_ru:  str = ""
    region:       str = "Qashqadaryo viloyati"
    region_ru:    str = ""
    phone:        str = ""
    is_disabled:  bool = False
    illness_info: str = ""
    card_number:  str = ""
    bio_uz:       str = ""
    bio_ru:       str = ""
    school_id:    Optional[int] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id:       int
    admin_id: int
    active:   bool
