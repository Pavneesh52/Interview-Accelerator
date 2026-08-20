from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Interview Agent API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/interview_agent",
        validation_alias="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    
    # JWT
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # File Storage (S3/MinIO)
    S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000",
        validation_alias="S3_ENDPOINT_URL"
    )
    S3_ACCESS_KEY: str = Field(
        default="minioadmin",
        validation_alias="S3_ACCESS_KEY"
    )
    S3_SECRET_KEY: str = Field(
        default="minioadmin",
        validation_alias="S3_SECRET_KEY"
    )
    S3_BUCKET_NAME: str = Field(
        default="interview-agent",
        validation_alias="S3_BUCKET_NAME"
    )
    S3_REGION: str = Field(
        default="us-east-1",
        validation_alias="S3_REGION"
    )
    
    # LLM Providers
    # NVIDIA Nemotron (self-hosted or API)
    NEMOTRON_API_BASE: str = Field(
        default="http://localhost:8001/v1",
        validation_alias="NEMOTRON_API_BASE"
    )
    NEMOTRON_API_KEY: str = Field(
        default="",
        validation_alias="NEMOTRON_API_KEY"
    )
    NEMOTRON_MODEL: str = "nvidia/nemotron-3-ultra-550b"
    
    # OpenAI (fallback)
    OPENAI_API_KEY: str = Field(
        default="",
        validation_alias="OPENAI_API_KEY"
    )
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Anthropic (fallback)
    ANTHROPIC_API_KEY: str = Field(
        default="",
        validation_alias="ANTHROPIC_API_KEY"
    )
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Google Gemini (fallback)
    GEMINI_API_KEY: str = Field(
        default="",
        validation_alias="GEMINI_API_KEY"
    )
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        validation_alias="CELERY_RESULT_BACKEND"
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()