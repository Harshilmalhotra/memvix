from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DEEPGRAM_API_KEY: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
