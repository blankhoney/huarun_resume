from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PLACEHOLDER_MARKERS = ("replace-", "replace_with", "change-me", "your-")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "sqlite+pysqlite:///./huarun.sqlite3"
    session_secret: str = "dev-session-secret"
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_api_key: str = ""
    minimax_model: str = "MiniMax-M2.7"
    demo_email: str = "demo@blankhoney.xyz"
    demo_password: str = "Demo123456!"
    app_timezone: str = "Asia/Shanghai"
    upload_dir: str = Field(default="uploads")
    max_upload_bytes: int = Field(default=5 * 1024 * 1024, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_production_settings(settings: Settings) -> None:
    if settings.app_env.lower() != "production":
        return

    issues = []
    if (
        settings.database_url.startswith("sqlite")
        or "huarun:huarun@" in settings.database_url
        or _has_placeholder(settings.database_url)
    ):
        issues.append("DATABASE_URL must use non-default production credentials")
    if (
        settings.session_secret
        in {"dev-session-secret", "replace-with-long-random-string", "change-me"}
        or len(settings.session_secret) < 32
        or _has_placeholder(settings.session_secret)
    ):
        issues.append("SESSION_SECRET must be a non-default value with at least 32 characters")
    if (
        settings.demo_password == "Demo123456!"
        or len(settings.demo_password) < 12
        or _has_placeholder(settings.demo_password)
    ):
        issues.append("DEMO_PASSWORD must be changed for production")

    if issues:
        raise RuntimeError("Production configuration is insecure: " + "; ".join(issues))


def _has_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)
