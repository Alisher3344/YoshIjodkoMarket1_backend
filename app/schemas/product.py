from typing import Optional
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name_uz:      str   = Field(..., description="O'zbek nomi")
    name_ru:      str   = ""
    desc_uz:      str   = ""
    desc_ru:      str   = ""
    price:        float = Field(..., gt=0)
    old_price:    Optional[float] = None
    stock:        int   = Field(1, ge=0)
    category:     str   = ""
    badge:        str   = ""
    author:       str   = ""
    author_ru:    str   = ""
    school:       str   = ""
    school_ru:    str   = ""
    grade:        str   = ""
    district:     str   = ""
    district_ru:  str   = ""
    region:       str   = ""
    region_ru:    str   = ""
    phone:        str   = ""
    student_type: str   = "normal"
    card_number:  str   = ""
    story_uz:     str   = ""
    story_ru:     str   = ""
    photo:        str   = ""
    image:        str   = ""
    rating:       float = 5.0
    reviews:      int   = 0
    sold:         int   = 0
    student_id:   Optional[int] = None


class ProductResponse(BaseModel):
    id:           int
    name_uz:      str
    name_ru:      str
    desc_uz:      str
    desc_ru:      str
    price:        float
    old_price:    Optional[float]
    stock:        int
    category:     str
    badge:        str
    author:       str
    author_ru:    str
    school:       str
    school_ru:    str
    grade:        str
    district:     str
    district_ru:  str
    region:       str
    region_ru:    str
    phone:        str
    student_type: str
    card_number:  str
    story_uz:     str
    story_ru:     str
    photo:        str
    image:        str
    rating:       float
    reviews:      int
    sold:         int
    student_id:   Optional[int] = None

    class Config:
        from_attributes = True