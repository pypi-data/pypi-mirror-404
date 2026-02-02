import getpass
import logging
import os
import socket
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Identity (Ed25519 key storage)
    identity_dir: str = "~/.hearth/worker/identity"

    controller_url: str = "ws://localhost:43110"

    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "hearth"

    cache_dir: str = "~/.hearth/worker/cache"
    cache_max_size_gb: int = 50

    spool_dir: str = "~/.hearth/worker/spool"
    spool_max_size_gb: int = 20

    runs_dir: str = "~/.hearth/worker/runs"

    heartbeat_interval: float = 30.0
    reconnect_delays: list[int] = [1, 2, 5, 10, 30, 60]
    max_concurrent_tasks: int = 1

    # SSH config for rsync fallback (optional, only needed when storage_mode=rsync)
    ssh_host: str | None = None  # If None, use machine's hostname
    ssh_port: int = 22
    ssh_user: str | None = None  # If None, use current user
    snapshot_inbox_path: str = "/tmp/hearth-inbox"  # Where rsync uploads go

    # HTTP API server config (for Controller to verify rsync uploads)
    api_host: str = "0.0.0.0"
    api_port: int = 43111
    api_secret: str | None = None  # Optional: if set, requires Bearer token auth

    def get_ssh_host(self) -> str | None:
        """Get SSH host. Returns None if not explicitly configured."""
        return self.ssh_host

    def get_ssh_user(self) -> str:
        """Get SSH user, falling back to current user if not configured."""
        return self.ssh_user or os.getenv("USER") or getpass.getuser()

    @field_validator("max_concurrent_tasks", mode="after")
    @classmethod
    def force_single_concurrency(cls, v: int) -> int:
        if v > 1:
            logger.warning("max_concurrent_tasks > 1 is not supported, forcing to 1")
            return 1
        return v

    class Config:
        env_prefix = "HEARTH_"
        env_file = ".env"
        extra = "ignore"  # Ignore controller-specific env vars


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
