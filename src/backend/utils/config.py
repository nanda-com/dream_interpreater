# src/backend/utils/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Explicitly define all fields you want to use from .env
    APP_NAME: str = "Dream Journal AI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Add specific fields you're using
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./dream_journal.db"
    JWT_SECRET: str = "your_jwt_secret"

    # Use model_config instead of Config in Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'  # This allows extra environment variables
    )

# Use a singleton pattern to ensure only one instance of settings
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings