import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenRouter Configuration
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Database
    database_url: str = "sqlite:///./wrx.db"
    
    # File storage
    data_path: str = "./data"
    manuscript_path: str = "./data/manuscript"
    codex_path: str = "./data/codex"
    
    # AI Model Configuration
    # Using OpenRouter models - these are popular models available through OpenRouter
    lore_archivist_model: str = "anthropic/claude-3.5-sonnet"
    grim_editor_model: str = "anthropic/claude-3.5-sonnet" 
    tone_metrics_model: str = "openai/gpt-4o-mini"
    default_model: str = "anthropic/claude-3.5-sonnet"
    
    class Config:
        env_file = ".env"

settings = Settings()
