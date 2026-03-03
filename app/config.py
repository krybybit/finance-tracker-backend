from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    WEBAPP_URL: str
    SECRET_KEY: str = "1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()