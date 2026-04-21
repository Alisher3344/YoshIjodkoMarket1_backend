from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    name:        str
    phone:       str
    password:    str
    school:      str = ""
    age:         int = 0
    is_disabled: bool = False
    card_number: Optional[str] = ""


class TokenResponse(BaseModel):
    token: str
    user:  dict