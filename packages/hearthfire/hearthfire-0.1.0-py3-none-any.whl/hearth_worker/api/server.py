import hashlib
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from hearth_worker.config import settings

# UUID v4 pattern for ticket validation (防止路径遍历)
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

# Maximum snapshot size (500 MB) - Worker 端验证
MAX_SNAPSHOT_SIZE = 500 * 1024 * 1024

if TYPE_CHECKING:
    from hearth_worker.cache.store import SnapshotCache

logger = logging.getLogger(__name__)

app = FastAPI(title="Hearth Worker API", version="0.1.0")

_cache: "SnapshotCache | None" = None


def set_cache(cache: "SnapshotCache") -> None:
    global _cache
    _cache = cache


async def verify_api_secret(authorization: str | None = Header(None)) -> None:
    """Verify API secret if configured. Allows unauthenticated if api_secret is not set."""
    if settings.api_secret:
        expected = f"Bearer {settings.api_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class HealthResponse(BaseModel):
    status: str


class VerifyResponse(BaseModel):
    verified: bool
    error: str | None = None
    expected: str | None = None
    actual: str | None = None
    snapshot_id: str | None = None
    cached: bool = False
    message: str | None = None


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/inbox/verify/{ticket}", response_model=VerifyResponse)
async def verify_inbox_file(
    ticket: str,
    expected_hash: str = Query(..., description="Expected snapshot_id (sha256:...)"),
    _: None = Depends(verify_api_secret),
) -> VerifyResponse:
    # 1. 验证 ticket 是有效 UUID（防止路径遍历攻击）
    if not UUID_PATTERN.match(ticket):
        raise HTTPException(status_code=400, detail="Invalid ticket format")

    # 2. 验证 expected_hash 格式 (sha256:64-hex-chars)
    if not expected_hash.startswith("sha256:") or len(expected_hash) != 71:
        raise HTTPException(status_code=400, detail="Invalid expected_hash format")
    if not re.match(r"^sha256:[0-9a-f]{64}$", expected_hash):
        raise HTTPException(status_code=400, detail="Invalid expected_hash format")

    if _cache is None:
        return VerifyResponse(verified=False, error="cache_not_initialized")

    # 3. 路径安全检查（防止路径遍历）
    inbox_path = Path(settings.snapshot_inbox_path).resolve()
    file_path = (inbox_path / f"{ticket}.tar.gz").resolve()

    # 确保文件路径在 inbox 目录内
    if not str(file_path).startswith(str(inbox_path) + "/"):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists():
        # 文件不在 inbox，检查是否已在 cache 中（幂等：重试时文件已被移入 cache）
        if _cache and _cache.get(expected_hash):
            logger.info(f"Inbox file not found but snapshot already cached: {expected_hash}")
            return VerifyResponse(
                verified=True,
                snapshot_id=expected_hash,
                cached=True,
                message="Already verified and cached",
            )
        logger.warning(f"Inbox file not found: {file_path}")
        return VerifyResponse(verified=False, error="file_not_found")

    # 4. 检查文件大小（Worker 端验证，防止绕过 Controller 限制）
    file_size = file_path.stat().st_size
    if file_size > MAX_SNAPSHOT_SIZE:
        # 删除超大文件并返回错误
        try:
            file_path.unlink()
            logger.warning(f"Deleted oversized inbox file: {file_path} ({file_size} bytes)")
        except OSError as e:
            logger.error(f"Failed to delete oversized file {file_path}: {e}")
        return VerifyResponse(
            verified=False,
            error="file_too_large",
        )

    # 5. 计算并验证 hash
    actual_hex = calculate_sha256(file_path)
    actual_hash = f"sha256:{actual_hex}"

    if actual_hash != expected_hash:
        # Delete invalid file to clean up inbox
        try:
            file_path.unlink()
            logger.warning(
                f"Deleted inbox file with hash mismatch: {file_path} "
                f"(expected={expected_hash}, actual={actual_hash})"
            )
        except OSError as e:
            logger.error(f"Failed to delete mismatched inbox file {file_path}: {e}")
        return VerifyResponse(
            verified=False,
            error="hash_mismatch",
            expected=expected_hash,
            actual=actual_hash,
        )

    # 6. 缓存 snapshot
    try:
        await _cache.store_from_file(expected_hash, file_path)
        logger.info(f"Verified and cached snapshot {expected_hash} from ticket {ticket}")
        return VerifyResponse(verified=True, snapshot_id=expected_hash, cached=True)
    except Exception as e:
        logger.exception(f"Failed to cache snapshot {expected_hash}")
        return VerifyResponse(verified=False, error=f"cache_error: {e}")
