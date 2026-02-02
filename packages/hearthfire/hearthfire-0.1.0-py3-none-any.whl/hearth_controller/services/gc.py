from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.db.models import Run, Snapshot
from hearth_controller.storage.client import StorageClient


class SnapshotGC:
    def __init__(
        self,
        db: AsyncSession,
        storage: StorageClient | None = None,
        max_age_days: int = 30,
        max_per_user: int = 50,
        grace_period_days: int = 7,
    ):
        self.db = db
        self.storage = storage
        self.max_age_days = max_age_days
        self.max_per_user = max_per_user
        self.grace_period_days = grace_period_days

    async def run(self) -> dict:
        protected = await self._get_protected_snapshots()
        to_delete = await self._find_deletable_snapshots(protected)

        deleted = 0
        freed_bytes = 0

        for snapshot in to_delete:
            try:
                await self._delete_snapshot(snapshot)
                deleted += 1
                freed_bytes += snapshot.size_bytes or 0
            except Exception:
                pass

        return {
            "deleted": deleted,
            "freed_mb": freed_bytes / (1024 * 1024),
            "protected": len(protected),
        }

    async def _get_protected_snapshots(self) -> set[str]:
        protected: set[str] = set()

        active_result = await self.db.execute(
            select(Run).where(Run.status.in_(["queued", "dispatched", "accepted", "running", "uploading"]))
        )
        for run in active_result.scalars():
            protected.add(run.snapshot_id)

        grace_threshold = datetime.now(timezone.utc) - timedelta(days=self.grace_period_days)
        recent_result = await self.db.execute(select(Run).where(Run.finished_at > grace_threshold))
        for run in recent_result.scalars():
            protected.add(run.snapshot_id)

        return protected

    async def _find_deletable_snapshots(self, protected: set[str]) -> list[Snapshot]:
        to_delete: list[Snapshot] = []
        user_counts: dict[str, int] = {}

        result = await self.db.execute(select(Snapshot).order_by(Snapshot.created_at.desc()))
        snapshots = result.scalars().all()

        age_threshold = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)

        for snapshot in snapshots:
            user_id = snapshot.owner_user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

            if snapshot.id in protected:
                continue

            if snapshot.created_at < age_threshold:
                to_delete.append(snapshot)
                continue

            if user_counts[user_id] > self.max_per_user:
                to_delete.append(snapshot)

        return to_delete

    async def _delete_snapshot(self, snapshot: Snapshot) -> None:
        if self.storage:
            try:
                await self.storage.delete(f"snapshots/{snapshot.id}/code.tar.gz")
                await self.storage.delete(f"snapshots/{snapshot.id}/manifest.json")
            except Exception:
                pass

        await self.db.delete(snapshot)
