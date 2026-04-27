from typing import Optional
from pydantic import BaseModel


class TelegramBotAuth(BaseModel):
    """Bot orqali kelgan autentifikatsiya (foydalanuvchi contact ulashganda).
    Bot hisoblanadi ishonchli — alohida HMAC tekshirilmaydi, lekin
    so'rov BOT_TOKEN bilan himoyalanadi (X-Bot-Token header)."""
    telegram_id: int
    phone:       str
    first_name:  Optional[str] = ""
    last_name:   Optional[str] = ""
    username:    Optional[str] = None  # Telegram username (ixtiyoriy)


class TelegramWebAppAuth(BaseModel):
    """Mini App ichidan Telegram.WebApp.initData qatorini yuboradi.
    Backend HMAC-SHA256 bilan tekshiradi."""
    init_data: str


class TelegramProfileUpdate(BaseModel):
    """Mini App ichida foydalanuvchi ism/familiya kiritganda"""
    name:      Optional[str] = None
    full_name: Optional[str] = None


class TelegramStudentRegister(BaseModel):
    """O'quvchi Mini App orqali ro'yxatdan o'tishi"""
    name:      str           # ism
    full_name: str = ""      # familiya
    grade:     str = ""      # sinf, masalan "4-A"
    school_id: int           # tanlangan maktab
    avatar:    str = ""      # base64 rasm


class TelegramProductCreate(BaseModel):
    """O'quvchi Mini App orqali mahsulot yuklashi"""
    name_uz:  str            # nom
    price:    float          # narx
    stock:    int = 1        # soni
    category: str = ""       # turi
    image:    str = ""       # base64 rasm
    desc_uz:  str = ""       # tavsif (ixtiyoriy)
