import json
import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from hearth_worker.config import settings

if TYPE_CHECKING:
    from hearth_worker.storage.client import StorageClient

logger = logging.getLogger(__name__)


@dataclass
class SpoolItem:
    id: str
    run_id: str
    attempt_id: str | None
    path: str
    data_path: Path
    created_at: float


class SpoolQueue:
    def __init__(self, spool_dir: Path | None = None, max_size_gb: int | None = None):
        self.spool_dir = spool_dir or Path(settings.spool_dir)
        self.max_size_gb = max_size_gb or settings.spool_max_size_gb
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.spool_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.meta_dir = self.spool_dir / "meta"
        self.meta_dir.mkdir(exist_ok=True)

    async def enqueue(self, run_id: str, attempt_id: str, path: str, data: bytes) -> str:
        item_id = uuid.uuid4().hex[:16]

        data_path = self.data_dir / item_id
        data_path.write_bytes(data)

        meta = {
            "id": item_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "path": path,
            "data_path": str(data_path),
            "created_at": os.path.getmtime(data_path),
        }
        meta_path = self.meta_dir / f"{item_id}.json"
        meta_path.write_text(json.dumps(meta))

        return item_id

    def list_items(self) -> list[SpoolItem]:
        items = []
        for meta_path in self.meta_dir.glob("*.json"):
            try:
                meta = json.loads(meta_path.read_text())
                items.append(
                    SpoolItem(
                        id=meta["id"],
                        run_id=meta["run_id"],
                        attempt_id=meta.get("attempt_id"),
                        path=meta["path"],
                        data_path=Path(meta["data_path"]),
                        created_at=meta["created_at"],
                    )
                )
            except Exception:
                continue
        return sorted(items, key=lambda x: x.created_at)

    async def drain(self, storage: "StorageClient") -> int:
        items = self.list_items()
        drained = 0

        for item in items:
            try:
                if not item.data_path.exists():
                    self._remove_item(item.id)
                    continue

                data = item.data_path.read_bytes()

                if item.attempt_id:
                    key = f"results/{item.run_id}/{item.attempt_id}/{item.path}"
                else:
                    logger.warning(
                        "Legacy spool item %s has no attempt_id, uploading to spool_legacy path",
                        item.id,
                    )
                    key = f"results/{item.run_id}/spool_legacy/{item.id}/{item.path}"

                await storage.upload(key, data)

                self._remove_item(item.id)
                drained += 1
            except Exception:
                break

        return drained

    def _remove_item(self, item_id: str) -> None:
        data_path = self.data_dir / item_id
        meta_path = self.meta_dir / f"{item_id}.json"

        if data_path.exists():
            data_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def get_size_gb(self) -> float:
        total = sum(f.stat().st_size for f in self.data_dir.glob("*"))
        return total / (1024**3)
