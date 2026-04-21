from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "yoshijodkor-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    DATABASE_URL: str = "sqlite+aiosqlite:///./yoshijodkor.db"
    CLIENT_URL: str = "http://localhost:5173"

    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()