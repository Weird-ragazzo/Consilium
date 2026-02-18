from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    nvidia_api_key_llama: str
    nvidia_api_key_llama2: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    model_a: str = "meta/llama-4-scout-17b-16e-instruct"
    model_b: str = "meta/llama-3.1-8b-instruct"

    max_tokens: int = 1024
    temperature: float = 0.7

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
