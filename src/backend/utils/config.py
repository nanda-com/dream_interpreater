from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Dream Journal AI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()