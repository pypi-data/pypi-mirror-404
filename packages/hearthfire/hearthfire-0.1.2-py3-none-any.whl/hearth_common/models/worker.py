from enum import Enum
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DRAINING = "draining"


class GPUInfo(BaseModel):
    index: int
    uuid: str
    name: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_percent: int
    temperature_c: Optional[int] = None
    labels: dict[str, str] = Field(default_factory=dict)


class WorkerInfo(BaseModel):
    id: str
    name: str
    tailscale_ip: str
    status: WorkerStatus
    cpu_cores: int
    memory_total_gb: float
    memory_used_gb: float
    disk_total_gb: float
    disk_used_gb: float
    gpus: list[GPUInfo]
    registration_expires_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None
    current_run_id: Optional[str] = None
    labels: dict[str, str] = Field(default_factory=dict)


class Heartbeat(BaseModel):
    worker_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    status: WorkerStatus
    memory_used_gb: float
    disk_used_gb: float
    gpus: list[GPUInfo]
    current_run_id: Optional[str] = None
    cached_snapshots: list[str] = Field(default_factory=list)
