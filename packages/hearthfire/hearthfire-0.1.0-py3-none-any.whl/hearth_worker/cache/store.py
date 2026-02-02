import asyncio
import shutil
import tempfile
from pathlib import Path

from hearth_worker.config import settings


class SnapshotCache:
    def __init__(self, cache_dir: Path | None = None, max_size_gb: int | None = None):
        self.cache_dir = cache_dir or Path(settings.cache_dir)
        self.max_size_gb = max_size_gb or settings.cache_max_size_gb
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def _get_lock(self, snapshot_id: str) -> asyncio.Lock:
        if snapshot_id not in self._locks:
            self._locks[snapshot_id] = asyncio.Lock()
        return self._locks[snapshot_id]

    def get(self, snapshot_id: str) -> Path | None:
        snapshot_path = self.cache_dir / f"{snapshot_id}.tar.gz"
        if snapshot_path.exists():
            return snapshot_path
        return None

    async def store(self, snapshot_id: str, data: bytes) -> Path:
        lock = self._get_lock(snapshot_id)
        async with lock:
            snapshot_path = self.cache_dir / f"{snapshot_id}.tar.gz"
            if snapshot_path.exists():
                return snapshot_path

            async with self._global_lock:
                await self._ensure_space(len(data))

            with tempfile.NamedTemporaryFile(
                dir=self.cache_dir, suffix=".tmp", delete=False
            ) as tmp:
                tmp.write(data)
                tmp_path = Path(tmp.name)

            tmp_path.replace(snapshot_path)
            return snapshot_path

    async def store_from_file(self, snapshot_id: str, source_path: Path) -> Path:
        """Store a snapshot from a local file (move instead of copy).

        Used for rsync-uploaded files in the inbox directory.
        The source file will be moved (not copied) to the cache.

        Args:
            snapshot_id: The snapshot identifier (sha256:...)
            source_path: Path to the source file (e.g., inbox/{ticket}.tar.gz)

        Returns:
            Path to the cached file
        """
        lock = self._get_lock(snapshot_id)
        async with lock:
            snapshot_path = self.cache_dir / f"{snapshot_id}.tar.gz"
            if snapshot_path.exists():
                # Already cached, remove source and return existing
                source_path.unlink(missing_ok=True)
                return snapshot_path

            async with self._global_lock:
                await self._ensure_space(source_path.stat().st_size)

            # Move file atomically using shutil.move
            # This handles cross-filesystem moves gracefully
            shutil.move(str(source_path), str(snapshot_path))
            return snapshot_path

    def list_snapshots(self) -> list[str]:
        return [p.stem.replace(".tar", "") for p in self.cache_dir.glob("*.tar.gz")]

    def get_size_gb(self) -> float:
        total = sum(f.stat().st_size for f in self.cache_dir.glob("*.tar.gz"))
        return total / (1024**3)

    async def _ensure_space(self, needed_bytes: int) -> None:
        needed_gb = needed_bytes / (1024**3)
        current_size = self.get_size_gb()

        if current_size + needed_gb <= self.max_size_gb:
            return

        files = sorted(
            self.cache_dir.glob("*.tar.gz"),
            key=lambda f: f.stat().st_mtime,
        )

        for file_path in files:
            if current_size + needed_gb <= self.max_size_gb * 0.8:
                break
            try:
                file_size = file_path.stat().st_size / (1024**3)
                file_path.unlink()
                current_size -= file_size
            except FileNotFoundError:
                pass

    def clear(self) -> None:
        for file_path in self.cache_dir.glob("*.tar.gz"):
            file_path.unlink()
