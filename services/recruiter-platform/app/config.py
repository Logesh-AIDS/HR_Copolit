from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Recruiter Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_URL: str = "postgresql://hr_user:hr_password@localhost:5432/hr_copilot"
    KAFKA_BROKER_URL: str = "localhost:9092"
    QDRANT_URL: str = "localhost"
    QDRANT_PORT: int = 6333
    
    class Config:
        env_file = ".env"

settings = Settings()
