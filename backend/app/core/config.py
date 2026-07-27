from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Character Conversation Pipeline"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://pipeline:pipeline@postgres:5432/pipeline"
    sync_database_url: str = "postgresql+psycopg2://pipeline:pipeline@postgres:5432/pipeline"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    encryption_master_key: str = "change-me-32-byte-fernet-key-base64="

    storage_backend: str = "local"
    storage_local_path: str = "/data/media"
    public_base_url: str = "http://localhost:8000"
    storage_s3_bucket: str = ""
    storage_s3_endpoint: str = ""
    storage_s3_access_key: str = ""
    storage_s3_secret_key: str = ""

    admin_username: str = "admin"
    admin_password: str = "change-me"

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
