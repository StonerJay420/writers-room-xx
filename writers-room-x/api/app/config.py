"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # API Keys
    openrouter_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///data/app.db"
    
    # Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    
    # Ports
    api_port: int = 8080
    ui_port: int = 3000
    
    # Git
    git_user_name: str = "Dev"
    git_user_email: str = "dev@example.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()