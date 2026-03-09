from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "GT Non-Conference Optimizer API"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    database_url: str = f"sqlite:///{(DATA_DIR / 'schedule_optimizer.db').as_posix()}"
    torvik_base_url: str = "https://www.barttorvik.com"
    torvik_ratings_path: str = "/trank.php"
    torvik_schedule_path: str = "/schedule.php"
    torvik_rate_limit_per_minute: int = 20
    torvik_cache_ttl_hours: int = 12
    torvik_timeout_seconds: int = 20
    use_mock_data: bool = Field(default=True, alias="USE_MOCK_DATA")
    gt_team_id: str = "GT"
    current_season: int = 2026

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()

