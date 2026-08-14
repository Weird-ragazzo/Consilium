from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""

    # Role-based model configuration
    model_router: str = "openai/gpt-oss-20b"
    model_safety: str = "openai/gpt-oss-safeguard-20b"
    model_simple: str = "openai/gpt-oss-20b"
    model_model1: str = "openai/gpt-oss-120b"
    model_model2: str = "openai/gpt-oss-20b"
    model_model3: str = "openai/gpt-oss-120b"
    model_vision: str = "qwen/qwen3.6-27b"

    max_tokens: int = 2048
    temperature: float = 0.3

    router_max_tokens: int = 64
    safety_max_tokens: int = 96
    extraction_max_tokens: int = 256
    simple_max_tokens: int = 256
    analysis_max_tokens: int = 768
    evidence_max_tokens: int = 768
    adjudication_max_tokens: int = 768
    final_safety_max_tokens: int = 96
    context_char_limit: int = 900
    evidence_char_limit: int = 1800
    adjudication_char_limit: int = 1200

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


settings = Settings()
