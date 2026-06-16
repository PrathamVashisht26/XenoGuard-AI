import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://xenoguard:xenoguard_pass@localhost:3306/xenoguard"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "./uploads"
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "ap-south-1"
    MAX_UPLOAD_SIZE_MB: int = 100
    CHUNK_SIZE_ROWS: int = 5000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://xenoguard.vercel.app"]
    APP_ENV: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
