from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'networking_ai.db'}"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_RETRIES: int = 3
    GROQ_RATE_LIMIT_DELAY: float = 2.0
    MAX_PROFILES_PER_RANK: int = 50
    DEFAULT_MAX_SEND_PER_DAY: int = 10

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


settings = Settings()
