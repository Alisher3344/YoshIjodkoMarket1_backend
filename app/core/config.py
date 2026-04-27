import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "yoshijodko-super-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:ralisher@localhost:5432/yoshijodkor")
    CLIENT_URL: str = os.getenv("CLIENT_URL", "http://localhost:5173")
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    # Telegram Mini App / Bot uchun
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MINIAPP_URL: str = os.getenv(
        "TELEGRAM_MINIAPP_URL", "https://yoshijodkor.uz"
    )


settings = Settings()