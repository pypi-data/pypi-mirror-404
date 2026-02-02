from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    RUNNING = "running"
    UPLOADING = "uploading"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class ResourceSpec(BaseModel):
    gpu: str = "any"
    gpu_memory_mb: Optional[int] = None
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    tags: list[str] = Field(default_factory=list)


class TaskSpec(BaseModel):
    command: str
    snapshot_id: str
    working_dir: str = "."
    resources: ResourceSpec = Field(default_factory=ResourceSpec)
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 3600
    max_attempts: int = 1


class TaskAttempt(BaseModel):
    id: str = Field(default_factory=lambda: new_id("att"))
    run_id: str
    attempt_number: int
    worker_id: Optional[str] = None
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = Field(default_factory=utc_now)
    dispatched_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stderr_tail: Optional[str] = None


class Run(BaseModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    owner_user_id: str
    name: Optional[str] = None
    spec: TaskSpec
    current_attempt: Optional[TaskAttempt] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    queue_position: Optional[int] = None
