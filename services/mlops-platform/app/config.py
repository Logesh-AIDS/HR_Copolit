from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MLOps Platform"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_URL: str = "postgresql://hr_user:hr_password@localhost:5432/hr_copilot"
    KAFKA_BROKER_URL: str = "localhost:9092"
    
    class Config:
        env_file = ".env"

settings = Settings()
