import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "infra/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    PROJECT_NAME: str = "ROBOLENS API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security & JWT
    SECRET_KEY: str = "robolens_super_secret_jwt_key_change_in_production_32charsmin"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://robolens_user:robolens_password@localhost:5432/robolens"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 Object Storage (MinIO or AWS)
    S3_ENDPOINT_URL: Optional[str] = "http://localhost:9000"
    S3_PUBLIC_ENDPOINT_URL: Optional[str] = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_REGION: str = "us-east-1"
    S3_BUCKET_RAW: str = "robolens-raw-media"
    S3_BUCKET_PROCESSED: str = "robolens-processed-media"
    S3_BUCKET_DATASETS: str = "robolens-datasets"
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = 3600

    # Temporal Workflow
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"


settings = Settings()
