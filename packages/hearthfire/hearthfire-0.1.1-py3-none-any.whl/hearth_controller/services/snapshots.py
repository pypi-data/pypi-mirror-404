import asyncio
import hashlib
import json
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.db.models import Snapshot
from hearth_controller.storage.client import StorageClient

_snapshot_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="snapshot")


class SnapshotService:
    EXCLUDE_PATTERNS: ClassVar[list[str]] = [
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
        "*.egg-info",
        ".env",
        ".env.*",
    ]

    def __init__(self, db: AsyncSession, storage: StorageClient | None = None):
        self.db = db
        self.storage = storage

    async def create_from_path(
        self,
        user_id: str,
        code_path: str,
        name: str | None = None,
    ) -> Snapshot:
        path = Path(code_path)
        if not path.exists():
            raise ValueError(f"Path not found: {code_path}")

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_snapshot_executor, self._create_tarball, path, tmp_path)

            content = await loop.run_in_executor(_snapshot_executor, tmp_path.read_bytes)
            snapshot_id = f"sha256:{hashlib.sha256(content).hexdigest()}"

            result = await self.db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
            existing = result.scalar_one_or_none()
            if existing:
                existing.last_used_at = datetime.now(timezone.utc)
                return existing

            git_info = await loop.run_in_executor(_snapshot_executor, self._get_git_info, path)

            manifest = self._create_manifest(snapshot_id, len(content), git_info)

            if self.storage:
                await self.storage.upload(
                    f"snapshots/{snapshot_id}/code.tar.gz",
                    content,
                )

                await self.storage.upload(
                    f"snapshots/{snapshot_id}/manifest.json",
                    json.dumps(manifest).encode(),
                )

            snapshot = Snapshot(
                id=snapshot_id,
                owner_user_id=user_id,
                name=name or path.name,
                size_bytes=len(content),
                source_type="local",
                git_repo=git_info.get("repo"),
                git_commit=git_info.get("commit"),
                git_branch=git_info.get("branch"),
                manifest=json.dumps(manifest),
            )
            self.db.add(snapshot)

            return snapshot

        finally:
            tmp_path.unlink(missing_ok=True)

    def _create_tarball(self, source_path: Path, output_path: Path) -> None:
        with tarfile.open(output_path, "w:gz") as tar:
            for item in source_path.rglob("*"):
                rel_path = item.relative_to(source_path)
                if self._should_exclude(rel_path):
                    continue

                if item.is_file():
                    tar.add(item, arcname=str(rel_path))

    def _should_exclude(self, rel_path: Path) -> bool:
        path_str = str(rel_path)

        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str.split("/"):
                return True

        return False

    def _create_manifest(self, snapshot_id: str, size: int, git_info: dict) -> dict:
        return {
            "snapshot_id": snapshot_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": git_info,
            "content": {
                "size_bytes": size,
                "excludes": self.EXCLUDE_PATTERNS,
            },
        }

    def _get_git_info(self, path: Path) -> dict:
        git_dir = path / ".git"
        if not git_dir.exists():
            return {"type": "local"}

        try:

            def git_cmd(cmd: list[str]) -> str | None:
                result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, check=False)
                return result.stdout.strip() if result.returncode == 0 else None

            return {
                "type": "git",
                "commit": git_cmd(["git", "rev-parse", "HEAD"]),
                "branch": git_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
                "dirty": bool(git_cmd(["git", "status", "--porcelain"])),
            }
        except Exception:
            return {"type": "local"}
