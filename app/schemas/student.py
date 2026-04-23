from pydantic import BaseModel


class StudentBase(BaseModel):
    name:         str
    full_name:    str = ""
    avatar:       str = ""
    age:          int = 0
    grade:        str = ""
    school:       str = ""
    phone:        str = ""
    is_disabled:  bool = False
    illness_info: str = ""
    card_number:  str = ""
    bio_uz:       str = ""


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id:       int
    admin_id: int
    active:   bool

    class Config:
        from_attributes = True