"""Storage mode API endpoints.

Provides information about the current storage configuration,
allowing clients (CLI/MCP) to determine which upload method to use.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from time import time
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.config import settings
from hearth_controller.db.models import HostMetricsLatest
from hearth_controller.db.session import get_db
from hearth_controller.storage.client import StorageClient

router = APIRouter()

# Cache for detected storage mode to avoid repeated checks
_storage_mode_cache: tuple[str, float] | None = None
CACHE_TTL = 30  # seconds


def _get_storage_client_or_none() -> StorageClient | None:
    """Get storage client from environment variables, or None if not configured."""
    endpoint = os.environ.get("HEARTH_STORAGE_ENDPOINT")
    access_key = os.environ.get("HEARTH_STORAGE_ACCESS_KEY")
    secret_key = os.environ.get("HEARTH_STORAGE_SECRET_KEY")
    bucket = os.environ.get("HEARTH_STORAGE_BUCKET")

    # If any required env var is missing, S3 is not configured
    if not all([endpoint, access_key, secret_key, bucket]):
        return None

    # Type narrowing: all values are guaranteed non-None here due to the check above
    return StorageClient(
        endpoint=endpoint,  # type: ignore[arg-type]
        access_key=access_key,  # type: ignore[arg-type]
        secret_key=secret_key,  # type: ignore[arg-type]
        bucket=bucket,  # type: ignore[arg-type]
    )


async def check_s3_available() -> bool:
    """Check if S3/OSS is available and healthy."""
    client = _get_storage_client_or_none()
    if not client:
        return False

    try:
        # Use asyncio.wait_for to add timeout (5 seconds)
        return await asyncio.wait_for(client.health_check(), timeout=5.0)
    except (TimeoutError, Exception):
        return False


async def check_rsync_available(db: AsyncSession) -> bool:
    """Check if there are any rsync-capable workers available.

    A worker is rsync-capable if it has reported:
    - ssh_host (for SSH connection)
    - snapshot_inbox_path (where to rsync files)
    - Recent heartbeat (within last 2 minutes)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
    result = await db.execute(
        select(HostMetricsLatest)
        .where(HostMetricsLatest.ssh_host.isnot(None))
        .where(HostMetricsLatest.snapshot_inbox_path.isnot(None))
        .where(HostMetricsLatest.updated_at > cutoff)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_detected_storage_mode(db: AsyncSession) -> str:
    """Get the detected storage mode with caching.

    Returns one of: "s3", "rsync", "unavailable"
    """
    global _storage_mode_cache

    now = time()
    if _storage_mode_cache and (now - _storage_mode_cache[1]) < CACHE_TTL:
        return _storage_mode_cache[0]

    # Check S3 first (preferred)
    if await check_s3_available():
        mode = "s3"
    # Then check rsync
    elif await check_rsync_available(db):
        mode = "rsync"
    else:
        mode = "unavailable"

    _storage_mode_cache = (mode, now)
    return mode


StorageMode = Literal["s3", "rsync", "unavailable"]


@router.get("/mode")
async def get_storage_mode(db: AsyncSession = Depends(get_db)):
    """Return the current storage mode.

    Clients use this to determine which upload method to use:
    - "s3": Use presigned URLs for direct S3/OSS upload
    - "rsync": Use rsync to upload directly to a worker's inbox
    - "unavailable": No storage backend available (auto mode only)

    Response includes:
    - mode: The effective storage mode to use
    - detected: Whether mode was auto-detected
    - configured: The configured storage_mode setting
    - error: Error message if mode is "unavailable"
    """
    if settings.storage_mode == "auto":
        # Auto-detect storage mode
        detected_mode = await get_detected_storage_mode(db)
        response = {
            "mode": detected_mode,
            "detected": True,
            "configured": "auto",
        }
        if detected_mode == "unavailable":
            response["error"] = "No storage backend available"
        return response
    else:
        # Explicit configuration
        return {
            "mode": settings.storage_mode,
            "detected": False,
            "configured": settings.storage_mode,
        }
