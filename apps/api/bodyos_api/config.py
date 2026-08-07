from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BODYOS_", env_file=None, extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite+pysqlite:///:memory:"
    encryption_key: SecretStr = SecretStr("")
    owner_token: SecretStr = SecretStr("")
    identity_pepper: SecretStr = SecretStr("")
    internal_token: SecretStr = SecretStr("")
    model_proxy_token: SecretStr = SecretStr("")
    public_base_url: str = "http://127.0.0.1:8000"
    codex_command: str = "codex"
    hermes_command: str = "hermes"
    hermes_model: str = "gpt-5.3-codex-spark"
    model_timeout_seconds: int = 120
    study_start_date: str = ""
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
