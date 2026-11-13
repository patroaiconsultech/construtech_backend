"""Configuracao exclusiva do backend comercial CONSTRUTECH."""
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONSTRUTECH_AGENT_", extra="ignore")
    enabled: bool = False
    openai_api_key: str = ""
    model: str = "gpt-5.4-mini-2026-03-17"
    frontend_origin: str = ""
    redis_url: str = ""
    max_hourly_requests: int = 20
    max_daily_requests: int = 80

    @model_validator(mode="after")
    def fail_closed(self):
        if not self.enabled:
            return self
        if not self.openai_api_key.strip():
            raise ValueError("agent_key_required")
        if not self.model.strip():
            raise ValueError("agent_model_required")
        parsed = urlsplit(self.frontend_origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("https_frontend_origin_required")
        if urlsplit(self.redis_url).scheme not in ("redis","rediss"):
            raise ValueError("redis_budget_store_required")
        if not (1 <= self.max_hourly_requests <= 100 and 1 <= self.max_daily_requests <= 500):
            raise ValueError("agent_limits_out_of_range")
        return self

settings = Settings()
