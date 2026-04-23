from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    name:      str                    # Ism
    full_name: Optional[str] = ""     # Familiya
    phone:     str                    # +998 XX XXX XX XX
    password:  str


class TokenResponse(BaseModel):
    token: str
    user:  dict