import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from hearth_controller.api.deps import CurrentUser, DBSession
from hearth_controller.api.hosts import resolve_host_id
from hearth_controller.db.models import Host, Run, RunLog, Snapshot

router = APIRouter()


class ResourceSpec(BaseModel):
    gpu: str = "any"
    gpu_memory_mb: int | None = None
    cpu_cores: int | None = None
    memory_mb: int | None = None
    tags: list[str] = Field(default_factory=list)


class RunCreate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=1024)
    command: str = Field(..., min_length=1)
    snapshot_id: str
    host_id: str = Field(..., min_length=1, description="Target host ID (required)")
    working_dir: str = "."
    resources: ResourceSpec = Field(default_factory=ResourceSpec)
    env: dict[str, str] = Field(default_factory=dict)
    client_request_id: str | None = Field(None, max_length=64)


def _compute_idempotency_fingerprint(body: RunCreate) -> str:
    """Compute stable hash of request parameters for idempotency check."""
    # Include all parameters that define the "intent" of the run
    # Exclude client_request_id itself
    data = {
        "snapshot_id": body.snapshot_id,
        "host_id": body.host_id,
        "command": body.command,
        "working_dir": body.working_dir,
        "resources": body.resources.model_dump(),
        "env": body.env,
        "name": body.name,
    }
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:32]


class RunResponse(BaseModel):
    id: str
    owner_user_id: str
    name: str | None
    description: str | None = None
    command: str
    working_dir: str
    work_path: str | None = None  # Absolute path on worker
    snapshot_id: str
    host_id: str | None
    host_name: str | None = None  # Populated from Host.name
    status: str
    attempt_number: int
    exit_code: int | None
    error_type: str | None
    error_message: str | None
    created_at: datetime
    dispatched_at: datetime | None
    accepted_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int


class RunLogResponse(BaseModel):
    content: str
    has_more: bool


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    db: DBSession,
    current_user: CurrentUser,
    body: RunCreate,
) -> RunResponse:
    """Create a new run (enqueue a task)."""

    # Resolve host_id prefix to full ID (Docker-style)
    resolved_host_id = await resolve_host_id(db, body.host_id)

    # Handle idempotency if client_request_id is provided
    if body.client_request_id:
        fingerprint = _compute_idempotency_fingerprint(body)

        # Check for existing run with same client_request_id
        result = await db.execute(
            select(Run).where(
                Run.owner_user_id == current_user.id,
                Run.client_request_id == body.client_request_id,
            )
        )
        existing_run = result.scalar_one_or_none()

        if existing_run:
            # Verify fingerprint matches (same request parameters)
            if existing_run.idempotency_fingerprint != fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="client_request_id already used with different parameters",
                )
            # Idempotent replay: return existing run
            return RunResponse.model_validate(existing_run)
    else:
        fingerprint = None

    # Verify snapshot exists
    result = await db.execute(select(Snapshot).where(Snapshot.id == body.snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found",
        )

    # Verify user owns the snapshot
    if snapshot.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this snapshot",
        )

    # Validate rsync affinity: snapshot must be on target host in rsync mode
    if snapshot.rsync_worker_id and snapshot.rsync_worker_id != resolved_host_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Snapshot was uploaded to host {snapshot.rsync_worker_id} but run targets {resolved_host_id}. "
            f"In rsync mode, snapshot and run must target the same host.",
        )

    # Verify target host exists and is active
    result = await db.execute(select(Host).where(Host.id == resolved_host_id))
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host '{resolved_host_id}' not found",
        )

    if host.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Host '{resolved_host_id}' is not active (status: {host.status})",
        )

    run = Run(
        id=uuid4().hex[:32],
        owner_user_id=current_user.id,
        name=body.name,
        description=body.description,
        command=body.command,
        working_dir=body.working_dir,
        snapshot_id=body.snapshot_id,
        host_id=resolved_host_id,
        resources=json.dumps(body.resources.model_dump()),
        env=json.dumps(body.env),
        status="queued",
        client_request_id=body.client_request_id,
        idempotency_fingerprint=fingerprint,
    )
    db.add(run)
    try:
        await db.flush()
    except IntegrityError:
        # Concurrent insert with same client_request_id
        await db.rollback()
        if body.client_request_id:
            # Re-fetch and return existing (idempotent behavior)
            result = await db.execute(
                select(Run).where(
                    Run.owner_user_id == current_user.id,
                    Run.client_request_id == body.client_request_id,
                )
            )
            existing_run = result.scalar_one_or_none()
            if existing_run:
                if existing_run.idempotency_fingerprint != fingerprint:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="client_request_id already used with different parameters",
                    )
                return RunResponse.model_validate(existing_run)
        # Unknown integrity error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create run due to database constraint",
        )

    return RunResponse.model_validate(run)


@router.get("", response_model=RunListResponse)
async def list_runs(
    db: DBSession,
    current_user: CurrentUser,
    status_filter: str | None = None,
    host_id: str | None = Query(None, description="Filter by host ID"),
    mine_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> RunListResponse:
    """List runs with optional filtering."""
    # Use selectinload to eagerly load host relationship for host_name
    query = select(Run).options(selectinload(Run.host))

    if mine_only:
        query = query.where(Run.owner_user_id == current_user.id)

    if status_filter:
        query = query.where(Run.status == status_filter)

    if host_id:
        query = query.where(Run.host_id == host_id)

    query = query.order_by(Run.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    runs = result.scalars().all()

    # Count total - apply ALL filters consistently
    count_query = select(func.count(Run.id))
    if mine_only:
        count_query = count_query.where(Run.owner_user_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Run.status == status_filter)
    if host_id:
        count_query = count_query.where(Run.host_id == host_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Build responses with host_name populated
    run_responses = []
    for r in runs:
        resp = RunResponse.model_validate(r)
        if r.host:
            resp.host_name = r.host.name
        run_responses.append(resp)

    return RunListResponse(
        runs=run_responses,
        total=total,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    db: DBSession,
    current_user: CurrentUser,
    run_id: str,
) -> RunResponse:
    """Get a run by ID."""
    result = await db.execute(select(Run).options(selectinload(Run.host)).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Enforce ownership
    if run.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this run",
        )

    resp = RunResponse.model_validate(run)
    if run.host:
        resp.host_name = run.host.name
    return resp


MAX_LOG_LIMIT = 5000  # Maximum logs per request


@router.get("/{run_id}/logs", response_model=RunLogResponse)
async def get_run_logs(
    db: DBSession,
    current_user: CurrentUser,
    run_id: str,
    offset: int = 0,
    limit: int = 1000,
) -> RunLogResponse:
    """Get logs for a run."""
    # Clamp limit to maximum
    limit = min(limit, MAX_LOG_LIMIT)

    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Enforce ownership
    if run.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this run",
        )

    # Get logs
    logs_result = await db.execute(
        select(RunLog)
        .where(RunLog.run_id == run_id)
        .order_by(RunLog.id)
        .offset(offset)
        .limit(limit + 1)
    )
    logs = logs_result.scalars().all()

    has_more = len(logs) > limit
    if has_more:
        logs = logs[:limit]

    content = "\n".join(log.content for log in logs)

    return RunLogResponse(content=content, has_more=has_more)


@router.post("/{run_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_run(
    db: DBSession,
    current_user: CurrentUser,
    run_id: str,
) -> None:
    """Cancel a run."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.owner_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this run",
        )

    # Idempotent: already canceling/canceled is a no-op (return 204)
    if run.status in ("canceling", "canceled"):
        return

    # Terminal states cannot be canceled
    if run.status in ("succeeded", "failed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run is already finished",
        )

    # Store host_id/attempt_id before modifying run
    host_id = run.host_id
    attempt_id = run.current_attempt_id

    if run.status == "queued":
        run.status = "canceled"
        run.finished_at = datetime.now(timezone.utc)
    elif run.status in ("dispatched", "accepted", "running", "uploading"):
        run.status = "canceling"
        run.cancel_requested_at = datetime.now(timezone.utc)

    # Commit first, then network I/O (ensures DB state is persisted before WS call)
    await db.commit()

    # Best-effort send cancel to worker if connected
    if run.status == "canceling" and host_id:
        from hearth_controller.ws.gateway import gateway

        await gateway.cancel_task(host_id, run_id, attempt_id)  # type: ignore[call-arg]


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    db: DBSession,
    current_user: CurrentUser,
    run_id: str,
) -> None:
    """Delete a run. Only completed/failed/canceled runs can be deleted."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.owner_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this run",
        )

    if run.status not in ("succeeded", "failed", "canceled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed, failed, or canceled runs can be deleted",
        )

    await db.delete(run)
    await db.commit()


@router.post("/{run_id}/retry", response_model=RunResponse)
async def retry_run(
    db: DBSession,
    current_user: CurrentUser,
    run_id: str,
) -> RunResponse:
    """Retry a failed run by creating a new run with the same parameters."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    original_run = result.scalar_one_or_none()

    if not original_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if original_run.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this run",
        )

    if original_run.status not in ("failed", "canceled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed or canceled runs",
        )

    new_run = Run(
        id=uuid4().hex[:32],
        owner_user_id=current_user.id,
        name=original_run.name,
        command=original_run.command,
        working_dir=original_run.working_dir,
        snapshot_id=original_run.snapshot_id,
        host_id=original_run.host_id,
        resources=original_run.resources,
        env=original_run.env,
        status="queued",
    )
    db.add(new_run)
    await db.flush()

    return RunResponse.model_validate(new_run)
