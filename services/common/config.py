# services/common/config.py
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    # Application Mode
    ENV: str = Field(default="development", validation_alias="ENV")
    DEBUG: bool = Field(default=True, validation_alias="DEBUG")
    PROJECT_NAME: str = Field(default="AI Interview Platform", validation_alias="PROJECT_NAME")
    API_V1_STR: str = Field(default="/api/v1", validation_alias="API_V1_STR")

    # Security
    SECRET_KEY: str = Field(
        default="SUPER_SECRET_RANDOM_KEY_CHANGE_THIS_IN_PRODUCTION_1234567890",
        validation_alias="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field(default="HS256", validation_alias="ALGORITHM")
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], validation_alias="ALLOWED_ORIGINS")

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql://hr_user:hr_password@127.0.0.1:5432/hr_copilot",
        validation_alias="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=10, validation_alias="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, validation_alias="DB_MAX_OVERFLOW")
    DB_POOL_RECYCLE: int = Field(default=1800, validation_alias="DB_POOL_RECYCLE")
    DB_POOL_TIMEOUT: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")

    # Redis Settings
    REDIS_URL: str = Field(
        default="redis://127.0.0.1:6379/0",
        validation_alias="REDIS_URL"
    )
    REDIS_POOL_SIZE: int = Field(default=20, validation_alias="REDIS_POOL_SIZE")

    # Rate Limiting Settings (Requests per minute per IP)
    RATE_LIMIT_RPM: int = Field(default=60, validation_alias="RATE_LIMIT_RPM")

    # Document Management & Storage Settings
    STORAGE_PROVIDER: str = Field(default="local", validation_alias="STORAGE_PROVIDER")
    LOCAL_STORAGE_DIR: str = Field(default="./storage", validation_alias="LOCAL_STORAGE_DIR")
    MAX_FILE_SIZE_MB: int = Field(default=10, validation_alias="MAX_FILE_SIZE_MB")

    # Infrastructure Services
    KAFKA_BROKER_URL: str = Field(default="localhost:9092", validation_alias="KAFKA_BROKER_URL")
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200", validation_alias="ELASTICSEARCH_URL")
    MINIO_ENDPOINT: str = Field(default="localhost:9000", validation_alias="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")

    # Model Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings instance
settings = CommonSettings()
