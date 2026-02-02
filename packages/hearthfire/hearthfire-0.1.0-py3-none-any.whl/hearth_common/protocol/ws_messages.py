from enum import Enum
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from hearth_common.protocol.version import PROTOCOL_VERSION


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_message_id() -> str:
    return uuid4().hex


class MessageType(str, Enum):
    # Handshake (challenge-response auth)
    CHALLENGE = "challenge"
    HELLO = "hello"
    WELCOME = "welcome"
    ERROR = "error"

    # Heartbeat
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"

    # Probes
    PROBE_REQUEST = "probe_request"
    PROBE_RESPONSE = "probe_response"

    # Tasks
    DISPATCH_TASK = "dispatch_task"
    CANCEL_TASK = "cancel_task"
    TASK_ACCEPTED = "task_accepted"
    TASK_STARTED = "task_started"
    TASK_UPLOADING = "task_uploading"
    TASK_LOG = "task_log"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELED = "task_canceled"

    # Legacy (to be deprecated)
    STORAGE_STATUS = "storage_status"


class WSMessage(BaseModel):
    type: MessageType
    payload: dict[str, Any]
    message_id: str = Field(default_factory=new_message_id)
    correlation_id: Optional[str] = None
    run_id: Optional[str] = None
    worker_id: Optional[str] = None
    seq: int
    timestamp: datetime = Field(default_factory=utc_now)


class HelloPayload(BaseModel):
    """Worker sends this after receiving CHALLENGE."""

    host_id: Optional[str] = None  # None for first registration
    public_key: str  # Base64-encoded Ed25519 public key
    signature: str  # Base64-encoded signature of nonce
    protocol_version: str = PROTOCOL_VERSION
    claims: dict[str, Any] = Field(default_factory=dict)  # {hostname, machine_id, dmi_uuid}
    hardware: dict[str, Any] = Field(default_factory=dict)  # {cpu_cores, memory_gb, ...}


class ChallengePayload(BaseModel):
    """Controller sends this immediately after connection."""

    nonce: str  # Random challenge to sign


class WelcomePayload(BaseModel):
    """Controller sends this after successful authentication."""

    host_id: str  # Assigned or existing host ID
    status: str  # "active" or "pending"
    protocol_version: str = PROTOCOL_VERSION
    heartbeat_interval: int = 30  # Seconds
    storage_config: Optional[dict[str, Any]] = None  # RustFS config
    probes: list[str] = Field(default_factory=list)  # Probes to run


class ErrorPayload(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: Optional[dict[str, Any]] = None


class ProbeRequestPayload(BaseModel):
    """Controller requests worker to run probes."""

    probes: list[str]  # List of probe names to run


class ProbeResponsePayload(BaseModel):
    """Worker sends probe results."""

    results: list[dict[str, Any]]  # List of probe results


class HeartbeatPayload(BaseModel):
    """Heartbeat message with optional metrics fields.

    All fields are optional to allow flexible heartbeat strategies:
    - Worker may send full metrics on every heartbeat
    - Worker may send liveness-only heartbeats with empty payload
    - Controller patch-updates only fields that are present
    """

    # Worker identification
    worker_id: Optional[str] = None
    status: Optional[str] = None

    # CPU metrics
    cpu_percent: Optional[float] = None

    # Memory metrics
    memory_used_gb: Optional[float] = None
    memory_total_gb: Optional[float] = None

    # Disk metrics
    disk_used_gb: Optional[float] = None
    disk_total_gb: Optional[float] = None

    # GPU metrics
    gpus: Optional[list[dict[str, Any]]] = None

    # Task state
    current_task_id: Optional[str] = None
    current_attempt_id: Optional[str] = None

    # Cache state
    cached_snapshots: Optional[list[str]] = None

    # SSH config for rsync fallback
    ssh_host: Optional[str] = None  # FQDN or IP for rsync connection
    ssh_port: Optional[int] = None  # SSH port (default 22)
    ssh_user: Optional[str] = None  # SSH username
    snapshot_inbox_path: Optional[str] = None  # Where rsync uploads go


class HeartbeatAckPayload(BaseModel):
    """Heartbeat acknowledgment."""

    pass


class DispatchTaskPayload(BaseModel):
    run_id: str
    attempt_id: str
    snapshot_id: str
    command: str
    working_dir: str = "."
    env: dict[str, str]
    timeout_seconds: int


class TaskLogPayload(BaseModel):
    run_id: str
    attempt_id: str
    stream_id: str = "main"
    chunk_index: int
    content: str
    stream: str = "stdout"


class TaskAcceptedPayload(BaseModel):
    run_id: str
    attempt_id: str


class TaskStartedPayload(BaseModel):
    run_id: str
    attempt_id: str


class TaskUploadingPayload(BaseModel):
    run_id: str
    attempt_id: str


class TaskCompletedPayload(BaseModel):
    run_id: str
    attempt_id: str
    exit_code: int


class TaskFailedPayload(BaseModel):
    run_id: str
    attempt_id: str
    error_type: str
    error_message: str
    stderr_tail: Optional[str] = None


class TaskCanceledPayload(BaseModel):
    """Worker sends this when a task is canceled (not failed)."""

    run_id: str
    attempt_id: str
    exit_code: int
