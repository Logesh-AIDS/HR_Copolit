from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Feature Platform"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_URL: str = "postgresql://hr_user:hr_password@localhost:5432/hr_copilot"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    KAFKA_BROKER_URL: str = "localhost:9092"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
