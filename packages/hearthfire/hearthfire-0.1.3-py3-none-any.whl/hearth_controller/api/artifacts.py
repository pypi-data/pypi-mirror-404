"""Artifacts API endpoints for listing and downloading run results by attempt."""

import os
from typing import Annotated

from botocore.config import Config as BotoConfig
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from hearth_controller.api.deps import CurrentUser
from hearth_controller.storage.client import StorageClient

router = APIRouter()


def get_storage_client() -> StorageClient:
    """Get storage client from environment variables."""
    endpoint = os.environ.get("HEARTH_STORAGE_ENDPOINT", "http://localhost:9000")
    access_key = os.environ.get("HEARTH_STORAGE_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("HEARTH_STORAGE_SECRET_KEY", "minioadmin")
    bucket = os.environ.get("HEARTH_STORAGE_BUCKET", "hearth")

    return StorageClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
    )


StorageClientDep = Annotated[StorageClient, Depends(get_storage_client)]


class ArtifactItem(BaseModel):
    """Artifact metadata."""

    key: str


class ArtifactListResponse(BaseModel):
    """Response for listing artifacts."""

    artifacts: list[ArtifactItem]


class ArtifactUrlResponse(BaseModel):
    """Response containing presigned URL for artifact download."""

    url: str


@router.get(
    "/{run_id}/attempts/{attempt_id}/artifacts",
    response_model=ArtifactListResponse,
)
async def list_artifacts(
    run_id: str,
    attempt_id: str,
    current_user: CurrentUser,
    storage: StorageClientDep,
) -> ArtifactListResponse:
    """List all artifacts for a specific run attempt."""
    prefix = f"results/{run_id}/{attempt_id}/"
    keys = await storage.list_objects(prefix)

    # Strip the prefix to return relative paths
    artifacts = [
        ArtifactItem(key=key[len(prefix) :] if key.startswith(prefix) else key) for key in keys
    ]

    return ArtifactListResponse(artifacts=artifacts)


@router.get(
    "/{run_id}/attempts/{attempt_id}/artifacts/{path:path}",
    response_model=ArtifactUrlResponse,
)
async def get_artifact(
    run_id: str,
    attempt_id: str,
    path: str,
    current_user: CurrentUser,
    storage: StorageClientDep,
) -> ArtifactUrlResponse:
    """Get a presigned URL for downloading a specific artifact."""
    key = f"results/{run_id}/{attempt_id}/{path}"

    # Check if artifact exists
    if not await storage.exists(key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    # Generate presigned URL
    async with storage._session.client(
        service_name="s3",
        endpoint_url=storage.endpoint,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        config=BotoConfig(signature_version="s3v4"),
    ) as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": storage.bucket, "Key": key},
            ExpiresIn=3600,  # 1 hour
        )

    return ArtifactUrlResponse(url=url)
