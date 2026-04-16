from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    WEBAPP_URL: str
    SECRET_KEY: str = "1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    DEBUG: bool = True
    
    model_config = SettingsConfigDict(env_file=".env")  

settings = Settings()