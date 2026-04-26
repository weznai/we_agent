from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://agent:123456@localhost:3306/my_agent_db?charset=utf8mb4"
    SECRET_KEY: str = "super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    UPLOAD_DIR: str = "./data/uploads"
    EMBEDDING_MODEL: str = "local"
    EMBEDDING_DIMENSION: int = 128
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    ORDER_API_BASE_URL: str = "http://121.43.198.13:8080"
    ORDER_API_KEY: str = ""


@lru_cache()
def get_settings():
    return Settings()
