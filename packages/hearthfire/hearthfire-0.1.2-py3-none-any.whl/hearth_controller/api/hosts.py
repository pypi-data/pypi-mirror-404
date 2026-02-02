import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from hearth_controller.api.deps import AdminUser, CurrentUser, DBSession
from hearth_controller.db.models import Host, HostIdentity, HostMetricsLatest
from hearth_controller.services.identity import HostStatus, IdentityError, IdentityService

router = APIRouter()


async def resolve_host_id(db, id_or_prefix: str) -> str:
    """
    Resolve a host ID or prefix to the full host ID (Docker-style).

    Args:
        db: Database session
        id_or_prefix: Full host ID or unique prefix

    Returns:
        Full host ID if exactly one match found

    Raises:
        HTTPException 404: If no matching host found
        HTTPException 400: If prefix matches multiple hosts (ambiguous)
    """
    # First, try exact match
    result = await db.execute(select(Host).where(Host.id == id_or_prefix))
    host = result.scalar_one_or_none()
    if host:
        return host.id

    # Try prefix match
    result = await db.execute(select(Host.id).where(Host.id.startswith(id_or_prefix)).limit(11))
    matching_ids = [row[0] for row in result.fetchall()]

    if len(matching_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host not found: '{id_or_prefix}'",
        )
    elif len(matching_ids) == 1:
        return matching_ids[0]
    else:
        # Ambiguous - show up to 10 matching IDs
        shown_ids = matching_ids[:10]
        more = " ..." if len(matching_ids) > 10 else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ambiguous host prefix '{id_or_prefix}' matches {len(matching_ids)} hosts: {', '.join(shown_ids)}{more}",
        )


logger = logging.getLogger(__name__)


class HostResponse(BaseModel):
    id: str
    name: str
    tailscale_ip: str | None
    status: str
    last_heartbeat_at: datetime | None
    cpu_cores: int | None
    memory_gb: float | None
    disk_gb: float | None
    gpu_name: str | None
    gpu_vram_gb: float | None
    gpu_count: int | None
    capabilities: dict[str, Any] | None
    labels: dict[str, str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HostIdentityResponse(BaseModel):
    id: str
    public_key: str
    fingerprint: str
    claims: dict[str, Any] | None
    created_at: datetime
    revoked_at: datetime | None
    last_seen_at: datetime | None

    class Config:
        from_attributes = True


class HostDetailResponse(HostResponse):
    identities: list[HostIdentityResponse]


class HostListResponse(BaseModel):
    hosts: list[HostResponse]
    total: int


class HostUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    labels: dict[str, str] | None = None


class GPUMetrics(BaseModel):
    name: str
    uuid: str | None
    memory_total_mb: int
    memory_used_mb: int
    utilization_percent: float | None


class HostMetricsResponse(BaseModel):
    host_id: str
    updated_at: datetime | None
    cpu_percent: float | None
    memory_used_gb: float | None
    memory_total_gb: float | None
    disk_used_gb: float | None
    disk_total_gb: float | None
    current_run_id: str | None
    gpus: list[GPUMetrics]
    cached_snapshots: list[str]
    # SSH config (from worker heartbeat)
    ssh_host: str | None = None
    ssh_port: int | None = None
    ssh_user: str | None = None
    snapshot_inbox_path: str | None = None
    api_port: int | None = None
    # Connection info (observed by controller)
    observed_remote_addr: str | None = None
    observed_remote_port: int | None = None
    observed_remote_at: datetime | None = None


def _host_to_response(host: Host) -> HostResponse:
    labels = {}
    if host.labels:
        try:
            labels = json.loads(host.labels)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in labels for host %s", host.id)
            labels = {}

    capabilities = None
    if host.capabilities:
        try:
            capabilities = json.loads(host.capabilities)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in capabilities for host %s", host.id)
            capabilities = None

    return HostResponse(
        id=host.id,
        name=host.name,
        tailscale_ip=host.tailscale_ip,
        status=host.status,
        last_heartbeat_at=host.last_heartbeat_at,
        cpu_cores=host.cpu_cores,
        memory_gb=host.memory_gb,
        disk_gb=host.disk_gb,
        gpu_name=host.gpu_name,
        gpu_vram_gb=host.gpu_vram_gb,
        gpu_count=host.gpu_count,
        capabilities=capabilities,
        labels=labels,
        created_at=host.created_at,
        updated_at=host.updated_at,
    )


@router.get("/pending", response_model=HostListResponse)
async def list_pending_hosts(
    db: DBSession,
    admin: AdminUser,
) -> HostListResponse:
    identity_service = IdentityService(db, auto_approve=False)
    hosts = await identity_service.list_pending_hosts()

    return HostListResponse(
        hosts=[_host_to_response(h) for h in hosts],
        total=len(hosts),
    )


def _select_best_host_per_hostname(hosts: list[Host]) -> list[Host]:
    """
    Deduplicate hosts by hostname, selecting the best host for each hostname.

    Selection policy:
    1. Prefer ACTIVE over OFFLINE/other statuses
    2. Most recent last_heartbeat_at among same status
    3. Tie-breaker: smallest host_id (stable sort)

    Hosts with empty/null hostname are NOT deduplicated (all returned).
    """
    from collections import defaultdict

    # Group by hostname
    hostname_groups: dict[str, list[Host]] = defaultdict(list)
    no_hostname: list[Host] = []

    for host in hosts:
        # Treat empty string as no hostname
        if not host.name or not host.name.strip():
            no_hostname.append(host)
        else:
            hostname_groups[host.name].append(host)

    result: list[Host] = []

    # Add all hosts without hostname (no deduplication)
    result.extend(no_hostname)

    # For each hostname group, select the best host
    for _hostname, group in hostname_groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue

        # Sort by: (is_active DESC, last_heartbeat DESC, host_id ASC)
        def sort_key(h: Host) -> tuple[int, float, str]:
            # is_active: 0 if ACTIVE (comes first), 1 otherwise
            is_active = 0 if h.status == HostStatus.ACTIVE.value else 1
            # last_heartbeat: negative timestamp (more recent = smaller = first)
            # None treated as very old (large positive number)
            if h.last_heartbeat_at:
                heartbeat_ts = -h.last_heartbeat_at.timestamp()
            else:
                heartbeat_ts = float("inf")
            # host_id: for stable tie-breaking
            return (is_active, heartbeat_ts, h.id)

        group.sort(key=sort_key)
        result.append(group[0])

    return result


@router.get("", response_model=HostListResponse)
async def list_hosts(
    db: DBSession,
    current_user: CurrentUser,
    status_filter: str | None = None,
    include_merged: bool = False,
    include_duplicates: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> HostListResponse:
    """
    List hosts with optional hostname deduplication.

    By default, returns one host per hostname (deduped). Use include_duplicates=true
    to return all raw hosts including duplicates with the same hostname.

    Selection policy for deduplication:
    - Prefer ACTIVE over OFFLINE
    - If multiple active, pick most recent heartbeat
    - Tie-breaker: stable sort by host_id
    """
    query = select(Host)
    count_query = select(func.count(Host.id))

    if status_filter:
        query = query.where(Host.status == status_filter)
        count_query = count_query.where(Host.status == status_filter)
    elif not include_merged:
        query = query.where(Host.status != HostStatus.MERGED.value)
        count_query = count_query.where(Host.status != HostStatus.MERGED.value)

    # For deduplication, we need to fetch all matching hosts first, then dedupe in memory
    # This is simpler than complex SQL grouping and handles edge cases better
    if include_duplicates:
        # No deduplication - use normal pagination
        query = query.order_by(Host.name).limit(limit).offset(offset)
        result = await db.execute(query)
        hosts = list(result.scalars().all())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
    else:
        # Fetch all matching hosts for deduplication
        query = query.order_by(Host.name)
        result = await db.execute(query)
        all_hosts = list(result.scalars().all())

        # Deduplicate by hostname
        deduped_hosts = _select_best_host_per_hostname(all_hosts)

        # Apply pagination to deduped results
        total = len(deduped_hosts)
        hosts = deduped_hosts[offset : offset + limit]

    return HostListResponse(
        hosts=[_host_to_response(h) for h in hosts],
        total=total,
    )


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(
    db: DBSession,
    current_user: CurrentUser,
    host_id: str,
) -> HostResponse:
    """Get a host by ID or unique prefix."""
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(select(Host).where(Host.id == resolved_id))
    host = result.scalar_one_or_none()

    # host is guaranteed to exist after resolve_host_id
    return _host_to_response(host)


@router.get("/{host_id}/metrics", response_model=HostMetricsResponse)
async def get_host_metrics(
    db: DBSession,
    current_user: CurrentUser,
    host_id: str,
) -> HostMetricsResponse:
    resolved_id = await resolve_host_id(db, host_id)
    host = await db.get(Host, resolved_id)
    # host is guaranteed to exist after resolve_host_id

    metrics = await db.get(HostMetricsLatest, resolved_id)

    gpus = []
    cached = []
    if metrics:
        if metrics.gpus_json:
            try:
                gpus = [GPUMetrics(**g) for g in json.loads(metrics.gpus_json)]
            except (json.JSONDecodeError, TypeError):
                pass
        if metrics.cached_snapshots_json:
            try:
                cached = json.loads(metrics.cached_snapshots_json)
            except json.JSONDecodeError:
                pass

    return HostMetricsResponse(
        host_id=resolved_id,
        updated_at=metrics.updated_at if metrics else None,
        cpu_percent=metrics.cpu_percent if metrics else None,
        memory_used_gb=metrics.memory_used_gb if metrics else None,
        memory_total_gb=metrics.memory_total_gb if metrics else None,
        disk_used_gb=metrics.disk_used_gb if metrics else None,
        disk_total_gb=metrics.disk_total_gb if metrics else None,
        current_run_id=metrics.current_run_id if metrics else None,
        gpus=gpus,
        cached_snapshots=cached,
        # SSH config (from worker heartbeat)
        ssh_host=metrics.ssh_host if metrics else None,
        ssh_port=metrics.ssh_port if metrics else None,
        ssh_user=metrics.ssh_user if metrics else None,
        snapshot_inbox_path=metrics.snapshot_inbox_path if metrics else None,
        api_port=metrics.api_port if metrics else None,
        # Connection info (observed by controller)
        observed_remote_addr=metrics.observed_remote_addr if metrics else None,
        observed_remote_port=metrics.observed_remote_port if metrics else None,
        observed_remote_at=metrics.observed_remote_at if metrics else None,
    )


@router.patch("/{host_id}", response_model=HostResponse)
async def update_host(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
    body: HostUpdate,
) -> HostResponse:
    """Update a host (admin only)."""
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(select(Host).where(Host.id == resolved_id))
    host = result.scalar_one_or_none()

    # host is guaranteed to exist after resolve_host_id
    if body.name is not None:
        host.name = body.name
    if body.labels is not None:
        host.labels = json.dumps(body.labels)

    await db.commit()
    await db.refresh(host)
    return _host_to_response(host)


@router.post("/{host_id}/drain", status_code=status.HTTP_204_NO_CONTENT)
async def drain_host(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
) -> None:
    """Put a host into draining mode (admin only)."""
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(select(Host).where(Host.id == resolved_id))
    host = result.scalar_one_or_none()

    # host is guaranteed to exist after resolve_host_id
    host.status = "draining"
    await db.commit()


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
) -> None:
    """Delete a host (admin only)."""
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(select(Host).where(Host.id == resolved_id))
    host = result.scalar_one_or_none()

    # host is guaranteed to exist after resolve_host_id
    await db.delete(host)
    await db.commit()


def _identity_to_response(identity: HostIdentity) -> HostIdentityResponse:
    claims = None
    if identity.claims:
        try:
            claims = json.loads(identity.claims)
        except json.JSONDecodeError:
            claims = None

    return HostIdentityResponse(
        id=identity.id,
        public_key=identity.public_key,
        fingerprint=identity.fingerprint,
        claims=claims,
        created_at=identity.created_at,
        revoked_at=identity.revoked_at,
        last_seen_at=identity.last_seen_at,
    )


def _host_to_detail_response(host: Host) -> HostDetailResponse:
    base = _host_to_response(host)
    identities = [_identity_to_response(i) for i in host.identities]

    return HostDetailResponse(
        **base.model_dump(),
        identities=identities,
    )


@router.get("/{host_id}/detail", response_model=HostDetailResponse)
async def get_host_detail(
    db: DBSession,
    current_user: CurrentUser,
    host_id: str,
) -> HostDetailResponse:
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(
        select(Host).options(selectinload(Host.identities)).where(Host.id == resolved_id)
    )
    host = result.scalar_one_or_none()

    # host is guaranteed to exist after resolve_host_id
    return _host_to_detail_response(host)


class ApproveHostResponse(BaseModel):
    host_id: str
    status: str
    message: str


@router.post("/{host_id}/approve", response_model=ApproveHostResponse)
async def approve_host(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
) -> ApproveHostResponse:
    resolved_id = await resolve_host_id(db, host_id)
    identity_service = IdentityService(db, auto_approve=False)

    try:
        host = await identity_service.approve_host(resolved_id)
        await db.commit()
        return ApproveHostResponse(
            host_id=host.id,
            status=host.status,
            message="Host approved successfully",
        )
    except IdentityError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


class MergeHostsRequest(BaseModel):
    source_host_id: str = Field(..., description="Host ID to merge from (will be marked as merged)")


class MergeHostsResponse(BaseModel):
    target_host_id: str
    source_host_id: str
    message: str


@router.post("/{host_id}/merge", response_model=MergeHostsResponse)
async def merge_hosts(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
    body: MergeHostsRequest,
) -> MergeHostsResponse:
    # Resolve both host IDs (target from path, source from body)
    resolved_target_id = await resolve_host_id(db, host_id)
    resolved_source_id = await resolve_host_id(db, body.source_host_id)

    identity_service = IdentityService(db, auto_approve=False)

    try:
        await identity_service.merge_hosts(resolved_target_id, resolved_source_id)
        await db.commit()
        return MergeHostsResponse(
            target_host_id=resolved_target_id,
            source_host_id=resolved_source_id,
            message="Hosts merged successfully",
        )
    except IdentityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class RevokeIdentityResponse(BaseModel):
    identity_id: str
    message: str


@router.post("/{host_id}/identities/{identity_id}/revoke", response_model=RevokeIdentityResponse)
async def revoke_identity(
    db: DBSession,
    admin: AdminUser,
    host_id: str,
    identity_id: str,
) -> RevokeIdentityResponse:
    resolved_id = await resolve_host_id(db, host_id)
    result = await db.execute(
        select(HostIdentity).where(
            HostIdentity.id == identity_id,
            HostIdentity.host_id == resolved_id,
        )
    )
    identity = result.scalar_one_or_none()

    if not identity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Identity not found",
        )

    identity_service = IdentityService(db, auto_approve=False)
    await identity_service.revoke_identity(identity_id)
    await db.commit()

    return RevokeIdentityResponse(
        identity_id=identity_id,
        message="Identity revoked successfully",
    )


class DuplicateCandidateResponse(BaseModel):
    id: str
    new_host_id: str
    existing_host_id: str
    score: int
    reasons: list[str]
    created_at: datetime
    resolved_at: datetime | None
    resolution: str | None


class DuplicateListResponse(BaseModel):
    candidates: list[DuplicateCandidateResponse]
    total: int


class ResolveDuplicateRequest(BaseModel):
    action: str


@router.get("/duplicates", response_model=DuplicateListResponse)
async def list_duplicate_candidates(
    db: DBSession,
    admin: AdminUser,
    resolved: bool = False,
) -> DuplicateListResponse:
    identity_service = IdentityService(db, auto_approve=False)
    candidates = await identity_service.list_duplicate_candidates(resolved=resolved)

    return DuplicateListResponse(
        candidates=[
            DuplicateCandidateResponse(
                id=c.id,
                new_host_id=c.new_host_id,
                existing_host_id=c.existing_host_id,
                score=c.score,
                reasons=json.loads(c.reasons_json) if c.reasons_json else [],
                created_at=c.created_at,
                resolved_at=c.resolved_at,
                resolution=c.resolution,
            )
            for c in candidates
        ],
        total=len(candidates),
    )


@router.post("/duplicates/{candidate_id}/resolve", response_model=DuplicateCandidateResponse)
async def resolve_duplicate(
    db: DBSession,
    admin: AdminUser,
    candidate_id: str,
    body: ResolveDuplicateRequest,
) -> DuplicateCandidateResponse:
    identity_service = IdentityService(db, auto_approve=False)
    try:
        candidate = await identity_service.resolve_duplicate(
            candidate_id=candidate_id,
            resolution=body.action,
            user_id=admin.id,
        )
        await db.commit()
        return DuplicateCandidateResponse(
            id=candidate.id,
            new_host_id=candidate.new_host_id,
            existing_host_id=candidate.existing_host_id,
            score=candidate.score,
            reasons=json.loads(candidate.reasons_json) if candidate.reasons_json else [],
            created_at=candidate.created_at,
            resolved_at=candidate.resolved_at,
            resolution=candidate.resolution,
        )
    except IdentityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
