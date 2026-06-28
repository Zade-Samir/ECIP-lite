## data which can be used further like environment variables, model paths, etc.

## Socho tumhare ghar me electricity hai. TV ko current chahiye. Fridge ko current chahiye. AC ko current chahiye. Har device ka apna wire nahi hota. Sab main switch board se current lete hain. settings.py wahi Main Switch Board hai. Project ka koi bhi module agar configuration chahta hai to usko yahi file milegi.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the entire ECIP application.
    Every module should read configuration from here.
    """

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    MODEL_NAME: str = "qwen3.5:9b"

    TEMPERATURE: float = 0.2

    TOP_P: float = 0.9

    MAX_TOKENS: int = 4096

    STREAM: bool = False

    SYSTEM_PROMPT: str = (
        "You are ECIP, an expert Java and Spring Boot Architect."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()