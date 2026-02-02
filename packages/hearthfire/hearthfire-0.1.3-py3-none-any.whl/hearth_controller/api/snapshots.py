import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiofiles
import httpx
from botocore.config import Config as BotoConfig
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from hearth_controller.api.artifacts import get_storage_client
from hearth_controller.api.deps import CurrentUser, DBSession
from hearth_controller.api.hosts import resolve_host_id
from hearth_controller.config import settings
from hearth_controller.db.models import HostMetricsLatest, Snapshot, utcnow

logger = logging.getLogger(__name__)

MAX_SNAPSHOT_SIZE = 500 * 1024 * 1024  # 500 MB

router = APIRouter()


class SnapshotPrepareRequest(BaseModel):
    """Request to prepare snapshot upload."""

    snapshot_id: str  # Format: sha256:<64-hex-chars>
    size_bytes: int
    name: str | None = None

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id(cls, v: str) -> str:
        if not re.match(r"^sha256:[0-9a-f]{64}$", v):
            raise ValueError("snapshot_id must be sha256:<64-hex-chars>")
        return v


class SnapshotConfirmRequest(BaseModel):
    """Request to confirm snapshot upload."""

    snapshot_id: str  # Format: sha256:<64-hex-chars>
    name: str | None = None
    size_bytes: int | None = None  # Optional, for validation
    manifest: dict | None = None  # Optional manifest data

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id(cls, v: str) -> str:
        if not re.match(r"^sha256:[0-9a-f]{64}$", v):
            raise ValueError("snapshot_id must be sha256:<64-hex-chars>")
        return v


class SnapshotConfirmResponse(BaseModel):
    """Response confirming snapshot registration."""

    snapshot_id: str
    created: bool  # True if newly created, False if already existed
    size_bytes: int


class SnapshotPrepareResponse(BaseModel):
    """Response with presigned upload URLs or existing snapshot confirmation."""

    snapshot_id: str
    already_exists: bool
    code_upload_url: str | None = None
    manifest_upload_url: str | None = None
    expires_in: int | None = None  # seconds


@router.post("/prepare", response_model=SnapshotPrepareResponse)
async def prepare_upload(
    request: SnapshotPrepareRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SnapshotPrepareResponse:
    """Prepare snapshot upload - returns presigned URLs for direct OSS upload.

    Client workflow:
    1. POST /prepare with snapshot metadata (hash, size)
    2. Receive presigned upload URLs (if not already exists)
    3. Upload tarball + manifest directly to OSS
    4. POST /confirm to register snapshot
    """
    # Validate size upfront to prevent storage abuse
    if request.size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="size_bytes must be positive",
        )
    if request.size_bytes > MAX_SNAPSHOT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Snapshot size {request.size_bytes} exceeds maximum {MAX_SNAPSHOT_SIZE} bytes",
        )

    # Check if snapshot already exists
    result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
    snapshot = result.scalar_one_or_none()

    if snapshot:
        # Verify ownership
        if snapshot.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )
        # Update last_used_at
        snapshot.last_used_at = utcnow()
        await db.commit()
        return SnapshotPrepareResponse(
            snapshot_id=request.snapshot_id,
            already_exists=True,
        )

    # Generate presigned PUT URLs for new snapshot
    storage = get_storage_client()
    expires_in = 3600  # 1 hour

    code_key = f"snapshots/{request.snapshot_id}/code.tar.gz"
    manifest_key = f"snapshots/{request.snapshot_id}/manifest.json"

    async with storage._session.client(
        service_name="s3",
        endpoint_url=storage.endpoint,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        config=BotoConfig(signature_version="s3v4"),
    ) as s3:
        code_url = await s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": storage.bucket, "Key": code_key},
            ExpiresIn=expires_in,
        )
        manifest_url = await s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": storage.bucket, "Key": manifest_key},
            ExpiresIn=expires_in,
        )

    return SnapshotPrepareResponse(
        snapshot_id=request.snapshot_id,
        already_exists=False,
        code_upload_url=code_url,
        manifest_upload_url=manifest_url,
        expires_in=expires_in,
    )


@router.post("/confirm", response_model=SnapshotConfirmResponse)
async def confirm_upload(
    request: SnapshotConfirmRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SnapshotConfirmResponse:
    """Confirm snapshot upload and register metadata.

    Called after client successfully uploads tarball to OSS.
    Verifies upload exists and registers snapshot in database.
    """
    # 1. Check if snapshot already exists
    result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
    existing = result.scalar_one_or_none()

    if existing:
        # Verify ownership
        if existing.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )
        # Update last_used_at and return (idempotent)
        existing.last_used_at = utcnow()
        await db.commit()
        return SnapshotConfirmResponse(
            snapshot_id=existing.id,
            created=False,
            size_bytes=existing.size_bytes,
        )

    # 2. Verify objects exist in storage
    storage = get_storage_client()
    code_key = f"snapshots/{request.snapshot_id}/code.tar.gz"
    manifest_key = f"snapshots/{request.snapshot_id}/manifest.json"

    code_exists = await storage.exists(code_key)
    manifest_exists = await storage.exists(manifest_key)

    if not code_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code tarball not found in storage: {code_key}",
        )
    if not manifest_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manifest not found in storage: {manifest_key}",
        )

    # 3. Get actual size from storage (HEAD request)
    async with storage._session.client(
        service_name="s3",
        endpoint_url=storage.endpoint,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        config=BotoConfig(signature_version="s3v4"),
    ) as s3:
        head_response = await s3.head_object(Bucket=storage.bucket, Key=code_key)
        actual_size = head_response.get("ContentLength", 0)

    # 4. Validate size limits
    if actual_size > MAX_SNAPSHOT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Snapshot size {actual_size} exceeds maximum {MAX_SNAPSHOT_SIZE} bytes",
        )

    # Optional: validate client-provided size matches
    if request.size_bytes and abs(request.size_bytes - actual_size) > 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Size mismatch: client={request.size_bytes}, actual={actual_size}",
        )

    # 5. Extract git info from manifest if provided
    git_repo = None
    git_commit = None
    git_branch = None
    git_dirty = None

    if request.manifest:
        source = request.manifest.get("source", {})
        git_repo = source.get("git_repo")
        git_commit = source.get("git_commit")
        git_branch = source.get("git_branch")
        git_dirty = source.get("git_dirty")

    # 6. Create Snapshot record
    snapshot = Snapshot(
        id=request.snapshot_id,
        owner_user_id=current_user.id,
        name=request.name or request.snapshot_id[:20],
        size_bytes=actual_size,
        source_type="direct",  # Uploaded directly by client
        git_repo=git_repo,
        git_commit=git_commit,
        git_branch=git_branch,
        git_dirty=git_dirty,
        manifest=json.dumps(request.manifest) if request.manifest else None,
        pinned=False,
        created_at=utcnow(),
        last_used_at=utcnow(),
    )

    db.add(snapshot)
    try:
        await db.commit()
    except IntegrityError:
        # Concurrent insert - another request already created this snapshot
        await db.rollback()
        # Re-fetch and return existing (idempotent behavior)
        result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
        existing = result.scalar_one_or_none()
        if existing and existing.owner_user_id == current_user.id:
            return SnapshotConfirmResponse(
                snapshot_id=existing.id,
                created=False,
                size_bytes=existing.size_bytes,
            )
        # Owned by another user (race condition)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Snapshot owned by another user",
        )

    return SnapshotConfirmResponse(
        snapshot_id=snapshot.id,
        created=True,
        size_bytes=snapshot.size_bytes,
    )


class SnapshotResponse(BaseModel):
    """Snapshot metadata response."""

    id: str
    name: str | None
    size_bytes: int
    source_type: str | None
    git_repo: str | None
    git_commit: str | None
    git_branch: str | None
    git_dirty: bool | None
    pinned: bool
    created_at: str
    last_used_at: str | None


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> SnapshotResponse:
    """Get snapshot metadata by ID.

    Returns snapshot details if owned by current user.
    """
    # Validate snapshot_id format
    if not re.match(r"^sha256:[0-9a-f]{64}$", snapshot_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid snapshot_id format. Must be sha256:<64-hex-chars>",
        )

    # Query snapshot
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found",
        )

    # Enforce ownership
    if snapshot.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Snapshot owned by another user",
        )

    return SnapshotResponse(
        id=snapshot.id,
        name=snapshot.name,
        size_bytes=snapshot.size_bytes,
        source_type=snapshot.source_type,
        git_repo=snapshot.git_repo,
        git_commit=snapshot.git_commit,
        git_branch=snapshot.git_branch,
        git_dirty=snapshot.git_dirty,
        pinned=snapshot.pinned,
        created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
        last_used_at=snapshot.last_used_at.isoformat() if snapshot.last_used_at else None,
    )


# =============================================================================
# Rsync Upload Mode: Two-phase prepare/confirm API
# =============================================================================


# In-memory lease store (MVP, can upgrade to Redis later for multi-instance)
@dataclass
class RsyncLease:
    """Represents a lease for rsync upload to a specific worker."""

    ticket: str
    worker_id: str
    snapshot_id: str
    size_bytes: int
    expires_at: datetime
    ssh_host: str
    ssh_port: int
    ssh_user: str
    inbox_path: str
    api_port: int
    owner_user_id: str  # User who created this lease (for security validation)


@dataclass
class _RsyncLeaseStore:
    """Thread-safe in-memory lease store with automatic expiration cleanup."""

    _leases: dict[str, RsyncLease] = field(default_factory=dict)

    def create(
        self,
        worker_id: str,
        snapshot_id: str,
        size_bytes: int,
        ssh_host: str,
        ssh_port: int,
        ssh_user: str,
        inbox_path: str,
        api_port: int,
        owner_user_id: str,
        ttl_seconds: int = 60,
    ) -> RsyncLease:
        """Create a new lease for rsync upload."""
        self._cleanup_expired()
        ticket = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        lease = RsyncLease(
            ticket=ticket,
            worker_id=worker_id,
            snapshot_id=snapshot_id,
            size_bytes=size_bytes,
            expires_at=now + timedelta(seconds=ttl_seconds),
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            ssh_user=ssh_user,
            inbox_path=inbox_path,
            api_port=api_port,
            owner_user_id=owner_user_id,
        )
        self._leases[ticket] = lease
        return lease

    def validate_and_consume(self, ticket: str, snapshot_id: str) -> RsyncLease | None:
        """Validate and consume a lease. Returns None if invalid/expired."""
        self._cleanup_expired()
        lease = self._leases.pop(ticket, None)
        if not lease:
            return None
        now = datetime.now(timezone.utc)
        if lease.expires_at < now:
            return None
        if lease.snapshot_id != snapshot_id:
            # Put it back - wrong snapshot_id
            self._leases[ticket] = lease
            return None
        return lease

    def get(self, ticket: str) -> RsyncLease | None:
        """Get a lease without consuming it."""
        self._cleanup_expired()
        return self._leases.get(ticket)

    def consume(self, ticket: str) -> RsyncLease | None:
        """Consume (remove) a lease after successful verification."""
        return self._leases.pop(ticket, None)

    def remove(self, ticket: str) -> None:
        """Remove a lease (e.g., expired or invalid)."""
        self._leases.pop(ticket, None)

    def _cleanup_expired(self) -> None:
        """Remove expired leases."""
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._leases.items() if v.expires_at < now]
        for k in expired:
            self._leases.pop(k, None)


# Global lease store instance
_rsync_lease_store = _RsyncLeaseStore()


class RsyncPrepareRequest(BaseModel):
    """Request to prepare rsync upload to a worker."""

    snapshot_id: str  # Format: sha256:<64-hex-chars>
    size_bytes: int
    host_id: str | None = Field(None, description="Target host for rsync (recommended)")

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id(cls, v: str) -> str:
        if not re.match(r"^sha256:[0-9a-f]{64}$", v):
            raise ValueError("snapshot_id must be sha256:<64-hex-chars>")
        return v


class RsyncPrepareResponse(BaseModel):
    """Response with worker SSH info for rsync upload."""

    snapshot_id: str
    already_exists: bool
    ticket: str | None = None  # UUID for confirm step
    worker_id: str | None = None
    ssh_host: str | None = None
    ssh_port: int | None = None
    ssh_user: str | None = None
    inbox_path: str | None = None
    expires_at: str | None = None  # ISO format
    ssh_host_source: str | None = None  # "configured" or "observed" (for debugging)


class RsyncConfirmRequest(BaseModel):
    """Request to confirm rsync upload completed."""

    snapshot_id: str  # Format: sha256:<64-hex-chars>
    ticket: str
    name: str | None = None
    manifest: dict | None = None

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id(cls, v: str) -> str:
        if not re.match(r"^sha256:[0-9a-f]{64}$", v):
            raise ValueError("snapshot_id must be sha256:<64-hex-chars>")
        return v


class RsyncConfirmResponse(BaseModel):
    """Response confirming rsync upload registration."""

    snapshot_id: str
    created: bool
    size_bytes: int
    worker_id: str


async def _select_worker_for_rsync(db, host_id: str | None = None) -> HostMetricsLatest | None:
    """Select an online worker with SSH configuration for rsync upload.

    If host_id is provided, selects that specific host (if rsync-capable).
    Otherwise falls back to random selection.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)

    # SSH capability: either configured ssh_host OR observed_remote_addr from connection
    ssh_capable = or_(
        HostMetricsLatest.ssh_host.isnot(None),
        HostMetricsLatest.observed_remote_addr.isnot(None),
    )

    if host_id:
        # Target specific host
        result = await db.execute(
            select(HostMetricsLatest)
            .where(HostMetricsLatest.host_id == host_id)
            .where(ssh_capable)
            .where(HostMetricsLatest.snapshot_inbox_path.isnot(None))
            .where(HostMetricsLatest.updated_at > cutoff)
        )
        return result.scalar_one_or_none()

    # Random selection fallback
    result = await db.execute(
        select(HostMetricsLatest)
        .where(ssh_capable)
        .where(HostMetricsLatest.snapshot_inbox_path.isnot(None))
        .where(HostMetricsLatest.updated_at > cutoff)
        .order_by(func.random())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/prepare-rsync", response_model=RsyncPrepareResponse)
async def prepare_rsync_upload(
    request: RsyncPrepareRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> RsyncPrepareResponse:
    """Prepare rsync upload - reserve a worker and return SSH info.

    Rsync upload workflow:
    1. POST /prepare-rsync with snapshot metadata (hash, size)
    2. Receive worker SSH info and ticket
    3. rsync code.tar.gz to worker's inbox directory
    4. POST /confirm-rsync with ticket to register snapshot

    Returns:
        RsyncPrepareResponse with SSH connection info or already_exists=True
    """
    # Validate size
    if request.size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="size_bytes must be positive",
        )
    if request.size_bytes > MAX_SNAPSHOT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Snapshot size {request.size_bytes} exceeds maximum {MAX_SNAPSHOT_SIZE} bytes",
        )

    # Check if snapshot already exists
    result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
    snapshot = result.scalar_one_or_none()

    if snapshot:
        # Verify ownership
        if snapshot.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )
        # Update last_used_at
        snapshot.last_used_at = utcnow()
        await db.commit()
        return RsyncPrepareResponse(
            snapshot_id=request.snapshot_id,
            already_exists=True,
        )

    # Resolve host_id prefix if provided
    resolved_host_id = None
    if request.host_id:
        resolved_host_id = await resolve_host_id(db, request.host_id)

    # Select a worker with SSH capability
    worker = await _select_worker_for_rsync(db, resolved_host_id)
    if not worker:
        if resolved_host_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Host {resolved_host_id} not available for rsync (offline or not configured)",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No workers available with rsync capability. Check worker SSH configuration.",
        )

    # Determine effective SSH host: prefer configured ssh_host, fall back to observed_remote_addr
    effective_ssh_host = worker.ssh_host or worker.observed_remote_addr
    ssh_host_source = "configured" if worker.ssh_host else "observed"

    if not effective_ssh_host:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Worker {worker.host_id} has no SSH address. Configure HEARTH_SSH_HOST on worker or ensure controller can see connection IP.",
        )

    # Create lease with effective host
    lease = _rsync_lease_store.create(
        worker_id=worker.host_id,
        snapshot_id=request.snapshot_id,
        size_bytes=request.size_bytes,
        ssh_host=effective_ssh_host,
        ssh_port=worker.ssh_port or 22,
        ssh_user=worker.ssh_user or "hearth",
        inbox_path=worker.snapshot_inbox_path,
        api_port=worker.api_port or 8765,
        owner_user_id=current_user.id,
        ttl_seconds=60,
    )

    return RsyncPrepareResponse(
        snapshot_id=request.snapshot_id,
        already_exists=False,
        ticket=lease.ticket,
        worker_id=lease.worker_id,
        ssh_host=lease.ssh_host,
        ssh_port=lease.ssh_port,
        ssh_user=lease.ssh_user,
        inbox_path=lease.inbox_path,
        expires_at=lease.expires_at.isoformat(),
        ssh_host_source=ssh_host_source,
    )


@router.post("/confirm-rsync", response_model=RsyncConfirmResponse)
async def confirm_rsync_upload(
    request: RsyncConfirmRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> RsyncConfirmResponse:
    """Confirm rsync upload and register snapshot.

    Called after client successfully rsyncs tarball to worker's inbox.
    Validates the ticket and creates the snapshot record.

    Retry-safe: ticket is only consumed after successful Worker verification.
    If verification fails or Worker is unreachable, client can retry.
    """
    # 1. Get lease WITHOUT consuming (allows retry on verification failure)
    lease = _rsync_lease_store.get(request.ticket)
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired ticket",
        )

    # Validate snapshot_id matches
    if lease.snapshot_id != request.snapshot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot ID mismatch",
        )

    # Validate owner_user_id matches (prevent ticket hijacking)
    if lease.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ticket belongs to another user",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if lease.expires_at < now:
        _rsync_lease_store.remove(request.ticket)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket expired",
        )

    # 2. Check if snapshot already exists (concurrent create)
    result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
    existing = result.scalar_one_or_none()

    if existing:
        # Verify ownership
        if existing.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )
        # Consume ticket since snapshot exists (no need for retry)
        _rsync_lease_store.consume(request.ticket)
        existing.last_used_at = utcnow()
        await db.commit()
        return RsyncConfirmResponse(
            snapshot_id=existing.id,
            created=False,
            size_bytes=existing.size_bytes,
            worker_id=lease.worker_id,
        )

    # 3. Call worker API to verify file exists and hash matches
    # NOTE: If this fails, ticket is NOT consumed, allowing client to retry
    worker_url = f"http://{lease.ssh_host}:{lease.api_port}"
    try:
        headers = {}
        if settings.worker_api_secret:
            headers["Authorization"] = f"Bearer {settings.worker_api_secret}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{worker_url}/inbox/verify/{request.ticket}",
                params={"expected_hash": request.snapshot_id},
                headers=headers,
            )

            # Check for non-2xx status before parsing JSON
            if not resp.is_success:
                body_preview = resp.text[:500] if resp.text else "(empty)"
                logger.error(
                    f"Worker verify failed: status={resp.status_code} "
                    f"ticket={request.ticket} snapshot={request.snapshot_id} "
                    f"worker={worker_url} body={body_preview}"
                )
                # Do NOT consume ticket - allow retry
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Worker returned error: {resp.status_code}",
                )

            # Parse JSON with error handling
            try:
                verify_result = resp.json()
            except (json.JSONDecodeError, ValueError) as e:
                body_preview = resp.text[:500] if resp.text else "(empty)"
                logger.error(
                    f"Worker returned invalid JSON: ticket={request.ticket} "
                    f"snapshot={request.snapshot_id} error={e} body={body_preview}"
                )
                # Do NOT consume ticket - allow retry
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Worker returned invalid response",
                )

            if not verify_result.get("verified"):
                error = verify_result.get("error", "unknown_error")
                logger.warning(f"Worker verification failed for {request.snapshot_id}: {error}")
                # Do NOT consume ticket - allow retry
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Verification failed: {error}",
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to contact worker API at {worker_url}: {e}")
        # Do NOT consume ticket - allow retry
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Worker API unreachable: {e}",
        )

    # 4. Verification succeeded - NOW consume the ticket
    _rsync_lease_store.consume(request.ticket)

    # 4. Extract git info from manifest if provided
    git_repo = None
    git_commit = None
    git_branch = None
    git_dirty = None

    if request.manifest:
        source = request.manifest.get("source", {})
        git_repo = source.get("git_repo")
        git_commit = source.get("git_commit")
        git_branch = source.get("git_branch")
        git_dirty = source.get("git_dirty")

    # 5. Create Snapshot record
    snapshot = Snapshot(
        id=request.snapshot_id,
        owner_user_id=current_user.id,
        name=request.name or request.snapshot_id[:20],
        size_bytes=lease.size_bytes,  # Use size from prepare request
        source_type="rsync",  # Mark as rsync-uploaded
        rsync_worker_id=lease.worker_id,  # Worker affinity for scheduling
        git_repo=git_repo,
        git_commit=git_commit,
        git_branch=git_branch,
        git_dirty=git_dirty,
        manifest=json.dumps(request.manifest) if request.manifest else None,
        pinned=False,
        created_at=utcnow(),
        last_used_at=utcnow(),
    )

    db.add(snapshot)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Re-fetch and return existing (idempotent behavior)
        result = await db.execute(select(Snapshot).where(Snapshot.id == request.snapshot_id))
        existing = result.scalar_one_or_none()
        if existing and existing.owner_user_id == current_user.id:
            return RsyncConfirmResponse(
                snapshot_id=existing.id,
                created=False,
                size_bytes=existing.size_bytes,
                worker_id=lease.worker_id,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Snapshot owned by another user",
        )

    return RsyncConfirmResponse(
        snapshot_id=snapshot.id,
        created=True,
        size_bytes=snapshot.size_bytes,
        worker_id=lease.worker_id,
    )


# =============================================================================
# Controller Relay Upload Mode: MCP uploads to Controller, Controller rsyncs to Worker
# =============================================================================


class UploadRelayResponse(BaseModel):
    """Response for relay upload."""

    status: str  # "confirmed" or "already_exists"
    snapshot_id: str
    worker_id: str | None = None


async def _verify_on_worker(
    ssh_host: str,
    api_port: int,
    ticket: str,
    snapshot_id: str,
) -> dict:
    """Verify that the uploaded file exists on worker and hash matches."""
    worker_url = f"http://{ssh_host}:{api_port}"
    try:
        headers = {}
        if settings.worker_api_secret:
            headers["Authorization"] = f"Bearer {settings.worker_api_secret}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{worker_url}/inbox/verify/{ticket}",
                params={"expected_hash": snapshot_id},
                headers=headers,
            )
            return resp.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to contact worker API at {worker_url}: {e}")
        return {"verified": False, "error": f"Worker API unreachable: {e}"}
    except Exception as e:
        logger.error(f"Worker verification error: {e}")
        return {"verified": False, "error": str(e)}


async def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file without loading it entirely into memory."""
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


@router.post("/upload-relay", response_model=UploadRelayResponse)
async def upload_relay(
    snapshot_id: str = Form(...),
    file: UploadFile = File(...),
    db: DBSession = ...,
    current_user: CurrentUser = ...,
) -> UploadRelayResponse:
    """
    Controller relay upload: MCP uploads file to Controller, Controller rsyncs to Worker.

    Use this when MCP doesn't have SSH key access to Workers.
    The file is uploaded via HTTPS to Controller, which then rsyncs it to a Worker.

    Args:
        snapshot_id: Snapshot ID in sha256:<64-hex-chars> format
        file: The tarball file to upload

    Returns:
        UploadRelayResponse with status and snapshot_id
    """
    # 1. Validate snapshot_id format
    if not re.match(r"^sha256:[0-9a-f]{64}$", snapshot_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid snapshot_id format. Must be sha256:<64-hex-chars>",
        )

    # 2. Check if already exists
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    existing = result.scalar_one_or_none()

    if existing:
        # Verify ownership
        if existing.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )
        # Update last_used_at
        existing.last_used_at = utcnow()
        await db.commit()
        return UploadRelayResponse(
            status="already_exists",
            snapshot_id=snapshot_id,
        )

    # 3. Stream file to temporary location (prevent OOM for large files)
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / f"{uuid.uuid4()}.tar.gz"
    total_size = 0

    try:
        # Stream write to temp file with size limit check
        # Use explicit read() loop for maximum compatibility across Starlette versions
        CHUNK_SIZE = 64 * 1024  # 64KB chunks
        async with aiofiles.open(tmp_path, "wb") as tmp:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_SNAPSHOT_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large: > {MAX_SNAPSHOT_SIZE} bytes",
                    )
                await tmp.write(chunk)

        # Verify hash (streaming calculation)
        actual_hash = await _calculate_file_hash(tmp_path)
        expected_hash = snapshot_id.replace("sha256:", "")
        if actual_hash != expected_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hash mismatch: expected {expected_hash}, got {actual_hash}",
            )

        # 4. Select a worker with SSH capability
        worker = await _select_worker_for_rsync(db)
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No workers available with rsync capability",
            )

        # 5. rsync to Worker
        ticket = str(uuid.uuid4())
        remote_path = (
            f"{worker.ssh_user or 'hearth'}@{worker.ssh_host}:"
            f"{worker.snapshot_inbox_path}/{ticket}.tar.gz"
        )

        rsync_cmd = [
            "rsync",
            "-avz",
            "-e",
            f"ssh -p {worker.ssh_port or 22} -o BatchMode=yes -o StrictHostKeyChecking=accept-new",
            str(tmp_path),
            remote_path,
        ]

        try:
            rsync_result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if rsync_result.returncode != 0:
                logger.error(f"rsync failed: {rsync_result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"rsync failed: {rsync_result.stderr}",
                )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="rsync upload timed out after 5 minutes",
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="rsync command not found on Controller",
            )

        # 6. Verify on Worker
        verify_result = await _verify_on_worker(
            worker.ssh_host,
            worker.api_port or 8765,
            ticket,
            snapshot_id,
        )
        if not verify_result.get("verified"):
            error_msg = verify_result.get("error", "unknown_error")
            logger.error(f"Worker verification failed for {snapshot_id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Worker verification failed: {error_msg}",
            )

        # 7. Create Snapshot record
        snapshot = Snapshot(
            id=snapshot_id,
            owner_user_id=current_user.id,
            name=snapshot_id[:20],
            size_bytes=total_size,
            source_type="relay",  # Mark as relay-uploaded
            rsync_worker_id=worker.host_id,  # Worker affinity for scheduling
            pinned=False,
            created_at=utcnow(),
            last_used_at=utcnow(),
        )

        db.add(snapshot)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Re-fetch and return existing (idempotent behavior)
            result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
            existing = result.scalar_one_or_none()
            if existing and existing.owner_user_id == current_user.id:
                return UploadRelayResponse(
                    status="already_exists",
                    snapshot_id=existing.id,
                    worker_id=worker.host_id,
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Snapshot owned by another user",
            )

        return UploadRelayResponse(
            status="confirmed",
            snapshot_id=snapshot.id,
            worker_id=worker.host_id,
        )

    finally:
        # Clean up temp file and directory
        if tmp_path.exists():
            tmp_path.unlink()
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
