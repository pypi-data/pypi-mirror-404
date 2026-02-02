from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    """
    User represents a human user who can authenticate and access the system.

    Authentication can be via:
    - Password (for web login) - stores Argon2id hash
    - API Token (for programmatic access) - managed via APIToken table
    """

    __tablename__ = "users"

    id = Column(String(32), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128))
    role = Column(String(16), default="user")  # "admin" or "user"
    status = Column(String(16), default="active")  # "active", "inactive", "locked"
    created_at = Column(DateTime, default=utcnow)
    last_seen_at = Column(DateTime)

    # Password authentication (Argon2id hash, nullable for service accounts)
    password_hash = Column(String(256), nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    # Brute-force protection
    failed_login_count = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    tokens = relationship("APIToken", back_populates="user", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="owner", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="owner", cascade="all, delete-orphan")


class APIToken(Base):
    """
    APIToken represents an authentication token for API access.

    Token kinds:
    - "api": Long-lived Personal Access Token (PAT) for CLI/programmatic use
    - "session_access": Short-lived access token from password login (15 min)
    - "session_refresh": Refresh token for session renewal (7 days)
    """

    __tablename__ = "api_tokens"

    id = Column(String(32), primary_key=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    token_hash = Column(String(64), nullable=False, index=True)
    prefix = Column(String(8), nullable=False)

    # Token type discriminator
    kind = Column(String(16), default="api", nullable=False, index=True)
    # Session identifier to link access + refresh tokens for clean logout
    session_id = Column(String(32), nullable=True, index=True)

    created_at = Column(DateTime, default=utcnow)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)

    user = relationship("User", back_populates="tokens")


class Host(Base):
    """
    Host represents a worker machine that can execute tasks.

    Host ID is stable and bound to cryptographic identity (public key),
    not to hostname, IP, or Tailscale node.
    """

    __tablename__ = "hosts"

    id = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    tailscale_ip = Column(String(64))
    status = Column(String(16), default="pending", index=True)  # pending, active, offline
    last_heartbeat_at = Column(DateTime)

    # Hardware info (reported by worker)
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    disk_gb = Column(Float)
    gpu_name = Column(String(128))
    gpu_vram_gb = Column(Float)
    gpu_count = Column(Integer, default=1)

    # Environment capabilities (JSON, detected by probes)
    capabilities = Column(Text)  # JSON: {"python": "3.11.5", "uv": "0.5.1", ...}

    # User-defined labels (JSON)
    labels = Column(Text)  # JSON: {"env": "production", "team": "ml"}

    # Legacy fields (to be deprecated)
    registration_expires_at = Column(DateTime)
    fingerprint = Column(Text)  # Legacy, use host_identities instead

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    runs = relationship("Run", back_populates="host")
    identities = relationship("HostIdentity", back_populates="host", cascade="all, delete-orphan")


class HostIdentity(Base):
    __tablename__ = "host_identities"

    id = Column(String(32), primary_key=True)
    host_id = Column(String(32), ForeignKey("hosts.id"), nullable=False, index=True)

    public_key = Column(String(128), nullable=False, unique=True, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    claims = Column(Text)

    machine_id = Column(String(64), index=True)
    dmi_uuid = Column(String(64), index=True)
    hostname = Column(String(128))
    hw_fingerprint = Column(String(64), index=True)

    created_at = Column(DateTime, default=utcnow)
    revoked_at = Column(DateTime)
    last_seen_at = Column(DateTime)

    host = relationship("Host", back_populates="identities")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String(80), primary_key=True)
    owner_user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128))
    size_bytes = Column(Integer, nullable=False)

    source_type = Column(String(16))
    git_repo = Column(String(256))
    git_commit = Column(String(64))
    git_branch = Column(String(128))
    git_dirty = Column(Boolean)

    # rsync mode: Worker ID where snapshot is cached (for affinity scheduling)
    # If set, scheduler MUST prefer this worker to avoid re-transfer
    rsync_worker_id = Column(String(32), ForeignKey("hosts.id"), nullable=True, index=True)

    manifest = Column(Text)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    last_used_at = Column(DateTime)

    owner = relationship("User", back_populates="snapshots")
    runs = relationship("Run", back_populates="snapshot")


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(32), primary_key=True)
    owner_user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    snapshot_id = Column(String(80), ForeignKey("snapshots.id"), nullable=False)
    host_id = Column(String(32), ForeignKey("hosts.id"), index=True)

    name = Column(String(128))
    description = Column(Text)
    command = Column(Text, nullable=False)
    working_dir = Column(String(256), default=".")
    resources = Column(Text)
    env = Column(Text)

    status = Column(String(16), default="queued", index=True)
    attempt_number = Column(Integer, default=1)
    current_attempt_id = Column(String(32))  # Tracks current dispatch attempt for correlation
    exit_code = Column(Integer)
    error_type = Column(String(64))
    error_message = Column(Text)
    work_path = Column(String(512))  # Absolute path on worker where task runs

    created_at = Column(DateTime, default=utcnow, index=True)
    dispatched_at = Column(DateTime)
    accepted_at = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    cancel_requested_at = Column(DateTime)  # Set when cancel is requested (status -> canceling)

    # Idempotency support
    client_request_id = Column(String(64), nullable=True, index=True)
    idempotency_fingerprint = Column(String(64), nullable=True)

    artifacts_uploaded = Column(Boolean, default=False)
    log_path = Column(String(256))

    owner = relationship("User", back_populates="runs")
    snapshot = relationship("Snapshot", back_populates="runs")
    host = relationship("Host", back_populates="runs")
    logs = relationship("RunLog", back_populates="run", cascade="all, delete-orphan")


class RunLog(Base):
    __tablename__ = "run_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(32), ForeignKey("runs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utcnow)
    content = Column(Text, nullable=False)
    stream = Column(String(16), default="stdout")

    run = relationship("Run", back_populates="logs")


class HostMetricsLatest(Base):
    """
    Latest metrics per host (single row, overwrites on each heartbeat).

    GUARDRAIL: Metrics are intentionally latest-only to prevent DB bloat.
    If metrics history is needed in the future, it MUST include:
    - TTL/retention policy (e.g., 24h, 7d)
    - Periodic cleanup job in reconciler
    - Configurable via METRICS_HISTORY_TTL_SECONDS

    DO NOT add a HostMetricsHistory table without these safeguards.
    """

    __tablename__ = "host_metrics_latest"

    host_id = Column(String(32), ForeignKey("hosts.id", ondelete="CASCADE"), primary_key=True)
    updated_at = Column(DateTime, nullable=False, index=True)

    cpu_percent = Column(Float)
    memory_used_gb = Column(Float)
    memory_total_gb = Column(Float)
    disk_used_gb = Column(Float)
    disk_total_gb = Column(Float)

    current_run_id = Column(String(32))
    gpus_json = Column(Text)
    cached_snapshots_json = Column(Text)

    ssh_host = Column(String(256))
    ssh_port = Column(Integer)
    ssh_user = Column(String(64))
    snapshot_inbox_path = Column(String(512))
    api_port = Column(Integer)

    # Observed remote address from WebSocket connection (controller-side observation)
    observed_remote_addr = Column(String(64))  # IP from websocket connection
    observed_remote_port = Column(Integer)
    observed_remote_at = Column(DateTime)


class HostDuplicateCandidate(Base):
    __tablename__ = "host_duplicate_candidates"

    id = Column(String(32), primary_key=True)
    new_host_id = Column(
        String(32), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    existing_host_id = Column(
        String(32), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    score = Column(Integer, nullable=False)
    reasons_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, index=True)
    resolution = Column(String(16))
    resolved_by_user_id = Column(String(32), ForeignKey("users.id"))
