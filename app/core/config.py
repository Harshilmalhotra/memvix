import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    
    BOT_TOKEN: str
    DEEPGRAM_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=[".env", f".env.{os.getenv('APP_ENV', 'dev')}"],
        env_ignore_empty=True,
        extra="ignore"
    )


settings = Settings()
