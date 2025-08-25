"""Configuration settings using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default="sqlite:///./wrx.db",
        alias="DATABASE_URL"
    )
    replica_db_url: Optional[str] = Field(
        default=None,
        alias="REPLICA_DB_URL"
    )
    auto_migrate: bool = Field(
        default=True,
        alias="AUTO_MIGRATE"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL"
    )
    
    # S3/Spaces
    s3_endpoint: Optional[str] = Field(default=None, alias="S3_ENDPOINT")
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET")
    s3_access_key: Optional[str] = Field(default=None, alias="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(default=None, alias="S3_SECRET_KEY")
    s3_cdn_domain: Optional[str] = Field(default=None, alias="S3_CDN_DOMAIN")
    s3_signing_secret: Optional[str] = Field(default=None, alias="S3_SIGNING_SECRET")
    
    # OpenRouter API
    openrouter_api_key: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_API_KEY"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL"
    )
    
    # Monitoring
    alert_webhook_url: Optional[str] = Field(default=None, alias="ALERT_WEBHOOK_URL")
    
    # App Settings
    app_name: str = Field(default="Writers Room X", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5000"],
        alias="CORS_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a single instance
settings = Settings()