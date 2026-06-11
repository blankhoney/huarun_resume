from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./huarun.sqlite3"
    session_secret: str = "dev-session-secret"
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_api_key: str = ""
    minimax_model: str = "MiniMax-M2.7"
    demo_email: str = "demo@blankhoney.xyz"
    demo_password: str = "Demo123456!"
    app_timezone: str = "Asia/Shanghai"
    upload_dir: str = Field(default="uploads")


@lru_cache
def get_settings() -> Settings:
    return Settings()
