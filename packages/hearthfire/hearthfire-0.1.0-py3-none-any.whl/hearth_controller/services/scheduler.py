import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.db.models import Host, Run


class Scheduler:
    """Scheduler with explicit host dispatch.

    Runs specify their target host_id at creation time.
    Scheduler dispatches to the specified host if it's active.
    If the host is offline, the run stays queued.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def _check_host_available(self, db: AsyncSession, host_id: str) -> Host | None:
        """Check if host exists and is active."""
        result = await db.execute(select(Host).where(Host.id == host_id, Host.status == "active"))
        return result.scalar_one_or_none()

    async def dispatch_next(self, db: AsyncSession) -> tuple[Run, Host] | None:
        """Try to dispatch the next queued run.

        Dispatches to the explicitly specified host_id.
        If host is offline/unavailable, run stays queued.
        """
        async with self._lock:
            # Get queued runs (FIFO order, limit to avoid scanning entire queue)
            result = await db.execute(
                select(Run).where(Run.status == "queued").order_by(Run.created_at).limit(10)
            )
            queued_runs = list(result.scalars().all())

            if not queued_runs:
                return None

            # Try each run in order until we find one that can be dispatched
            for run in queued_runs:
                if not run.host_id:
                    # Run has no host_id - this shouldn't happen with new API
                    # but handle gracefully by skipping
                    continue

                host = await self._check_host_available(db, run.host_id)
                if host:
                    # Host is active, dispatch this run
                    run.status = "dispatched"
                    run.dispatched_at = datetime.now(timezone.utc)
                    return run, host

            # No run could be dispatched (all target hosts offline)
            return None

    async def get_queue_position(self, db: AsyncSession, run_id: str) -> int | None:
        """Get the queue position for a run."""
        result = await db.execute(
            select(Run).where(Run.status == "queued").order_by(Run.created_at)
        )
        runs = result.scalars().all()

        for i, run in enumerate(runs):
            if run.id == run_id:
                return i + 1

        return None


# Global scheduler instance
scheduler = Scheduler()
