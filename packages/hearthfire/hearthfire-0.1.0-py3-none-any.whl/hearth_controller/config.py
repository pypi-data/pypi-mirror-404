from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


def _default_db_path() -> str:
    """Return expanded path for SQLite database."""
    db_path = Path.home() / ".hearth" / "controller" / "hearth.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path}"


class Settings(BaseSettings):
    database_url: str = _default_db_path()

    # Storage mode: "s3" for presigned URL uploads, "rsync" for direct rsync to worker
    # "auto" mode detects S3 availability first, falls back to rsync if unavailable
    storage_mode: Literal["s3", "rsync", "auto"] = "auto"

    # Worker API secret (shared secret for authenticating Controller -> Worker API calls)
    worker_api_secret: str | None = None

    token_prefix: str = "hth_"
    token_bytes: int = 32
    token_default_expiry_days: int = 90
    token_max_expiry_days: int = 365

    # Session token settings (for password login)
    session_access_minutes: int = 15
    session_refresh_days: int = 7

    # Security settings
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    min_password_length: int = 8

    cors_origins: list[str] = ["*"]

    # GC settings: run_logs cleanup (lightweight, prevents SQLite bloat)
    run_logs_retention_days: int = 7
    run_logs_gc_batch_size: int = 5000

    # GC settings: snapshot cleanup interval
    snapshot_gc_interval_hours: int = 1

    ws_handshake_timeout: float = 10.0
    ws_heartbeat_interval: float = 30.0

    # Worker registration: auto-approve new workers (set True for development)
    worker_auto_approve: bool = True

    host: str = "0.0.0.0"
    port: int = 43110

    class Config:
        env_prefix = "HEARTH_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
