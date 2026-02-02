"""
Reconciler - Background service for system consistency.

Responsibilities:
1. Check worker liveness: Mark hosts OFFLINE if no heartbeat for 60s
2. Handle stuck tasks: Re-queue DISPATCHED tasks that haven't started within 30s
3. Handle stuck uploads: Fail UPLOADING tasks that haven't completed within timeout
4. Dispatch queued tasks: Continuously try to match queued runs to available hosts

Architecture note:
- DB operations are committed BEFORE network I/O (broadcasts/dispatches)
- This prevents ghost dispatches and pool exhaustion
- If network I/O fails after commit, stuck-task recovery handles it
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.config import settings
from hearth_controller.db.models import Host, Run, RunLog
from hearth_controller.db.session import async_session_maker
from hearth_controller.ws.client_gateway import get_client_gateway

logger = logging.getLogger(__name__)


@dataclass
class ReconcileResult:
    """Result of a reconcile cycle, used to trigger side effects after commit."""

    offline_hosts: list[tuple[str, str]] = field(
        default_factory=list
    )  # [(host_id, host_name), ...]
    requeued_dispatched: list[tuple[str, int]] = field(
        default_factory=list
    )  # [(run_id, attempt), ...]
    requeued_accepted: list[tuple[str, int]] = field(
        default_factory=list
    )  # [(run_id, attempt), ...]
    requeued_from_offline: list[tuple[str, int]] = field(
        default_factory=list
    )  # [(run_id, attempt), ...]
    failed_running: list[str] = field(default_factory=list)  # [run_id, ...]
    failed_uploading_offline: list[str] = field(default_factory=list)  # [run_id, ...]
    failed_uploading_timeout: list[str] = field(default_factory=list)  # [run_id, ...]
    force_canceled: list[str] = field(default_factory=list)  # [run_id, ...]
    dispatched: list[tuple[str, str, str]] = field(
        default_factory=list
    )  # [(run_id, host_id, host_name), ...]


class Reconciler:
    """Background reconciliation service for system health."""

    # Configuration
    HEARTBEAT_TIMEOUT = 60  # seconds - mark host offline after this
    # 90s = 3x heartbeat interval, reduces false requeue risk
    DISPATCH_TIMEOUT = 90  # seconds - re-queue dispatched task after this
    ACCEPT_START_TIMEOUT = 60  # seconds - fail accepted-but-never-started task
    UPLOADING_TIMEOUT = 300  # seconds - fail uploading task after this (5 min)
    CANCELING_TIMEOUT = 120  # seconds - fail canceling task after this
    CHECK_INTERVAL = 10  # seconds - how often to run checks

    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None
        # GC timing counters (lightweight, prevents SQLite bloat)
        self._loop_counter = 0
        self._last_snapshot_gc_at: datetime | None = None

    async def start(self) -> None:
        """Start the reconciler background loop."""
        if self._running:
            logger.warning("Reconciler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"Reconciler started (heartbeat_timeout={self.HEARTBEAT_TIMEOUT}s, "
            f"dispatch_timeout={self.DISPATCH_TIMEOUT}s, "
            f"uploading_timeout={self.UPLOADING_TIMEOUT}s, "
            f"interval={self.CHECK_INTERVAL}s)"
        )

    async def stop(self) -> None:
        """Stop the reconciler background loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Reconciler stopped")

    async def _run_loop(self) -> None:
        """Main reconciliation loop."""
        while self._running:
            try:
                await self._reconcile()
                self._loop_counter += 1
            except Exception as e:
                logger.exception(f"Reconciler error: {e}")

            await asyncio.sleep(self.CHECK_INTERVAL)

    async def _reconcile(self) -> None:
        """Run all reconciliation checks.

        Architecture:
        1. Phase 1 (DB): All state transitions happen in one transaction
        2. Phase 2 (Network): Broadcasts and dispatches happen AFTER commit
        3. Phase 3 (SnapshotGC): Separate session, safe to be slow (storage I/O)
        This prevents ghost dispatches and long-held transactions.
        """
        result = ReconcileResult()
        should_run_snapshot_gc = False

        # Phase 1: DB operations
        async with async_session_maker() as session:
            try:
                offline_host_ids = await self._check_worker_liveness(session, result)
                await self._handle_tasks_on_offline_hosts(session, offline_host_ids, result)
                await self._check_stuck_dispatched(session, result)
                await self._check_stuck_accepted(session, result)
                await self._check_stuck_uploading(session, result)
                await self._check_stuck_canceling(session, result)
                await self._dispatch_queued_tasks(session, result)

                # GC: run_logs cleanup (every 6 loops = ~60s, lightweight, prevents SQLite bloat)
                if self._loop_counter % 6 == 0:
                    await self._gc_run_logs(session)

                # Check if snapshot GC is due (just set flag, don't run)
                should_run_snapshot_gc = self._should_run_snapshot_gc()

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception(f"Reconcile transaction failed: {e}")
                raise

        # Phase 2: Network I/O (after commit)
        await self._broadcast_results(result)

        # Phase 3: SnapshotGC (after commit, separate session, safe to be slow)
        if should_run_snapshot_gc:
            await self._run_snapshot_gc()

    async def _check_worker_liveness(
        self, session: AsyncSession, result: ReconcileResult
    ) -> list[str]:
        """
        Check worker heartbeats and mark stale hosts as OFFLINE.

        A host is considered offline if:
        - Status is 'active'
        - last_heartbeat_at < now - HEARTBEAT_TIMEOUT

        Returns list of host IDs that were marked offline.
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.HEARTBEAT_TIMEOUT)

        # Find and update stale hosts
        stmt_result = await session.execute(
            update(Host)
            .where(Host.status == "active")
            .where(Host.last_heartbeat_at < threshold)
            .values(status="offline", updated_at=datetime.now(timezone.utc))
            .returning(Host.id, Host.name)
        )

        stale_hosts = stmt_result.fetchall()
        offline_host_ids: list[str] = []

        for host_id, host_name in stale_hosts:
            logger.warning(
                f"Host {host_name} ({host_id}) marked offline: "
                f"no heartbeat for {self.HEARTBEAT_TIMEOUT}s"
            )
            result.offline_hosts.append((host_id, host_name))
            offline_host_ids.append(host_id)

        return offline_host_ids

    async def _handle_tasks_on_offline_hosts(
        self, session: AsyncSession, offline_host_ids: list[str], result: ReconcileResult
    ) -> None:
        """
        Handle tasks that were running/dispatched/accepted on hosts that just went offline.

        Strategy:
        - DISPATCHED tasks: Requeue (worker never started them)
        - ACCEPTED tasks: Requeue (worker accepted but never started them)
        - RUNNING tasks: Fail with error message (we can't know their state)
        - UPLOADING tasks: Fail with error message (upload was interrupted)

        Note: We could implement retry for RUNNING tasks in the future,
        but failing is the safer default to avoid duplicate execution.
        """
        if not offline_host_ids:
            return

        # Requeue dispatched tasks (safe to retry)
        dispatched_stmt = await session.execute(
            update(Run)
            .where(Run.host_id.in_(offline_host_ids))
            .where(Run.status == "dispatched")
            .values(
                status="queued",
                host_id=None,
                dispatched_at=None,
                attempt_number=Run.attempt_number + 1,
            )
            .returning(Run.id, Run.attempt_number)
        )

        for run_id, attempt in dispatched_stmt.fetchall():
            logger.warning(f"Run {run_id} requeued: host went offline (attempt #{attempt})")
            result.requeued_from_offline.append((run_id, attempt))

        # Requeue accepted tasks (safe to retry - worker accepted but never started)
        accepted_stmt = await session.execute(
            update(Run)
            .where(Run.host_id.in_(offline_host_ids))
            .where(Run.status == "accepted")
            .values(
                status="queued",
                host_id=None,
                dispatched_at=None,
                accepted_at=None,
                attempt_number=Run.attempt_number + 1,
            )
            .returning(Run.id, Run.attempt_number)
        )

        for run_id, attempt in accepted_stmt.fetchall():
            logger.warning(f"Run {run_id} requeued: host went offline (attempt #{attempt})")
            result.requeued_from_offline.append((run_id, attempt))

        # Fail running tasks (unsafe to retry - may have side effects)
        running_stmt = await session.execute(
            update(Run)
            .where(Run.host_id.in_(offline_host_ids))
            .where(Run.status == "running")
            .values(
                status="failed",
                error_type="host_lost",
                error_message="Host went offline while task was running",
                finished_at=datetime.now(timezone.utc),
            )
            .returning(Run.id)
        )

        for (run_id,) in running_stmt.fetchall():
            logger.warning(f"Run {run_id} failed: host went offline during execution")
            result.failed_running.append(run_id)

        # Fail uploading tasks (upload was interrupted)
        uploading_stmt = await session.execute(
            update(Run)
            .where(Run.host_id.in_(offline_host_ids))
            .where(Run.status == "uploading")
            .values(
                status="failed",
                error_type="host_lost",
                error_message="Host went offline during upload",
                finished_at=datetime.now(timezone.utc),
            )
            .returning(Run.id)
        )

        for (run_id,) in uploading_stmt.fetchall():
            logger.warning(f"Run {run_id} failed: host went offline during upload")
            result.failed_uploading_offline.append(run_id)

    async def _check_stuck_dispatched(self, session: AsyncSession, result: ReconcileResult) -> None:
        """
        Check for stuck DISPATCHED tasks and re-queue them.

        A task is considered stuck if:
        - Status is 'dispatched'
        - dispatched_at < now - DISPATCH_TIMEOUT
        - started_at IS NULL (task was never actually started by worker)

        Recovery action:
        - Set status back to 'queued'
        - Clear host_id assignment
        - Increment attempt_number

        Uses atomic UPDATE with conditions to prevent race with worker TASK_STARTED.
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.DISPATCH_TIMEOUT)

        # Atomic update with returning - prevents race conditions
        stmt_result = await session.execute(
            update(Run)
            .where(Run.status == "dispatched")
            .where(Run.dispatched_at < threshold)
            .where(Run.started_at.is_(None))  # Only requeue if never started
            .values(
                status="queued",
                host_id=None,
                dispatched_at=None,
                attempt_number=Run.attempt_number + 1,  # SQL-level increment
            )
            .returning(Run.id, Run.attempt_number)
        )

        for run_id, attempt in stmt_result.fetchall():
            logger.warning(
                f"Run {run_id} re-queued: stuck in DISPATCHED for {self.DISPATCH_TIMEOUT}s "
                f"(attempt #{attempt})"
            )
            result.requeued_dispatched.append((run_id, attempt))

    async def _check_stuck_accepted(self, session: AsyncSession, result: ReconcileResult) -> None:
        """
        Check for stuck ACCEPTED tasks and re-queue them.

        A task is considered stuck if:
        - Status is 'accepted'
        - accepted_at < now - ACCEPT_START_TIMEOUT
        - started_at IS NULL (task was never actually started by worker)

        Recovery action:
        - Set status back to 'queued'
        - Clear host_id and timestamps
        - Increment attempt_number

        This handles the case where a worker accepts a task but crashes or
        disconnects before sending TASK_STARTED. Re-queueing is safer than
        failing because no actual work has been done yet.
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.ACCEPT_START_TIMEOUT)

        stmt_result = await session.execute(
            update(Run)
            .where(Run.status == "accepted")
            .where(Run.accepted_at < threshold)
            .where(Run.started_at.is_(None))
            .values(
                status="queued",
                host_id=None,
                dispatched_at=None,
                accepted_at=None,
                attempt_number=Run.attempt_number + 1,
            )
            .returning(Run.id, Run.attempt_number)
        )

        for run_id, attempt in stmt_result.fetchall():
            logger.warning(
                f"Run {run_id} re-queued: stuck in ACCEPTED for {self.ACCEPT_START_TIMEOUT}s "
                f"(attempt #{attempt})"
            )
            result.requeued_accepted.append((run_id, attempt))

    async def _check_stuck_uploading(self, session: AsyncSession, result: ReconcileResult) -> None:
        """
        Check for stuck UPLOADING tasks and fail them.

        A task is considered stuck if:
        - Status is 'uploading'
        - started_at < now - UPLOADING_TIMEOUT (using started_at as proxy since
          uploading happens after running, so started_at + timeout is a safe bound)

        Recovery action:
        - Set status to 'failed'
        - Set error message indicating upload timeout
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.UPLOADING_TIMEOUT)

        stmt_result = await session.execute(
            update(Run)
            .where(Run.status == "uploading")
            .where(Run.started_at < threshold)
            .values(
                status="failed",
                error_type="timeout",
                error_message="Upload timeout: task stuck in uploading state",
                finished_at=datetime.now(timezone.utc),
            )
            .returning(Run.id)
        )

        for (run_id,) in stmt_result.fetchall():
            logger.warning(f"Run {run_id} failed: stuck in UPLOADING for {self.UPLOADING_TIMEOUT}s")
            result.failed_uploading_timeout.append(run_id)

    async def _check_stuck_canceling(self, session: AsyncSession, result: ReconcileResult) -> None:
        """
        Check for stuck CANCELING tasks and mark them as canceled.

        A task is considered stuck if:
        - Status is 'canceling'
        - cancel_requested_at < now - CANCELING_TIMEOUT
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.CANCELING_TIMEOUT)

        stmt_result = await session.execute(
            update(Run)
            .where(Run.status == "canceling")
            .where(Run.cancel_requested_at.isnot(None))
            .where(Run.cancel_requested_at < threshold)
            .values(
                status="canceled",
                error_message="Cancel timeout: task did not respond to cancel request",
                finished_at=datetime.now(timezone.utc),
            )
            .returning(Run.id)
        )

        for (run_id,) in stmt_result.fetchall():
            logger.warning(
                f"Run {run_id} force-canceled: stuck in CANCELING for {self.CANCELING_TIMEOUT}s"
            )
            result.force_canceled.append(run_id)

    async def _dispatch_queued_tasks(self, session: AsyncSession, result: ReconcileResult) -> None:
        """
        Try to dispatch queued tasks to available hosts.

        This is the scheduling loop that matches queued runs with eligible hosts.
        Uses the Scheduler's scoring model to pick the best host for each task.

        Note: Actual websocket dispatch happens in _broadcast_results after commit.
        Here we only update DB state and collect dispatch info.
        """
        from hearth_controller.services.scheduler import scheduler

        max_dispatches_per_cycle = 10  # Limit to prevent blocking too long

        while len(result.dispatched) < max_dispatches_per_cycle:
            # Try to dispatch next queued task
            dispatch_result = await scheduler.dispatch_next(session)
            if dispatch_result is None:
                # No more tasks to dispatch or no eligible hosts
                break

            run, host = dispatch_result
            logger.info(f"Scheduled run {run.id} to host {host.name} ({host.id})")
            result.dispatched.append((run.id, host.id, host.name))

    async def _gc_run_logs(self, session: AsyncSession) -> None:
        """
        Clean up old run_logs entries to prevent SQLite bloat.

        Strategy (lightweight, prevents unbounded DB growth):
        - Delete logs older than run_logs_retention_days (default 7 days)
        - Batch delete using LIMIT to avoid long transactions
        - Only cleans run_logs, not runs table
        """
        threshold = datetime.now(timezone.utc) - timedelta(days=settings.run_logs_retention_days)
        batch_size = settings.run_logs_gc_batch_size

        # Find IDs to delete in batches (SQLite doesn't support LIMIT in DELETE directly)
        stmt = select(RunLog.id).where(RunLog.timestamp < threshold).limit(batch_size)
        result = await session.execute(stmt)
        ids_to_delete = [row[0] for row in result.fetchall()]

        if ids_to_delete:
            await session.execute(delete(RunLog).where(RunLog.id.in_(ids_to_delete)))
            logger.info(
                f"GC: Deleted {len(ids_to_delete)} run_logs entries "
                f"(older than {settings.run_logs_retention_days} days)"
            )

    def _should_run_snapshot_gc(self) -> bool:
        """Check if enough time has passed since last snapshot GC."""
        now = datetime.now(timezone.utc)
        interval = timedelta(hours=settings.snapshot_gc_interval_hours)
        if self._last_snapshot_gc_at is not None:
            if now - self._last_snapshot_gc_at < interval:
                return False
        return True

    async def _run_snapshot_gc(self) -> None:
        """Run SnapshotGC in a separate session (safe to be slow)."""
        from hearth_controller.services.gc import SnapshotGC
        from hearth_controller.api.artifacts import get_storage_client

        self._last_snapshot_gc_at = datetime.now(timezone.utc)

        try:
            async with async_session_maker() as session:
                storage = get_storage_client()
                gc = SnapshotGC(db=session, storage=storage)
                gc_result = await gc.run()
                await session.commit()
                if gc_result["deleted"] > 0:
                    logger.info(
                        f"SnapshotGC: Deleted {gc_result['deleted']} snapshots, "
                        f"freed {gc_result['freed_mb']:.2f} MB"
                    )
        except Exception as e:
            logger.warning(f"SnapshotGC failed: {e}")

    async def _broadcast_results(self, result: ReconcileResult) -> None:
        """
        Broadcast all state changes to frontend and dispatch tasks to workers.

        This runs AFTER the DB transaction is committed, so all state is consistent.
        If a dispatch fails, the task stays in 'dispatched' state and will be
        recovered by _check_stuck_dispatched on the next cycle.
        """
        from hearth_controller.ws.gateway import gateway

        client_gw = get_client_gateway()

        # Broadcast host offline events
        for host_id, host_name in result.offline_hosts:
            await client_gw.broadcast_host_status(host_id, "offline", host_name)

        # Broadcast requeued tasks (from stuck dispatched)
        for run_id, _ in result.requeued_dispatched:
            await client_gw.broadcast_run_status(run_id, "queued")

        # Broadcast requeued tasks (from offline hosts)
        for run_id, _ in result.requeued_from_offline:
            await client_gw.broadcast_run_status(run_id, "queued")

        # Broadcast failed running tasks
        for run_id in result.failed_running:
            await client_gw.broadcast_run_status(run_id, "failed")

        # Broadcast failed uploading tasks (offline)
        for run_id in result.failed_uploading_offline:
            await client_gw.broadcast_run_status(run_id, "failed")

        # Broadcast failed uploading tasks (timeout)
        for run_id in result.failed_uploading_timeout:
            await client_gw.broadcast_run_status(run_id, "failed")

        # Broadcast force-canceled tasks (stuck in canceling)
        for run_id in result.force_canceled:
            await client_gw.broadcast_run_status(run_id, "canceled")

        # Dispatch tasks to workers and broadcast
        for run_id, host_id, host_name in result.dispatched:
            success = await gateway.dispatch_task_by_id(run_id, host_id)
            if success:
                logger.info(f"Dispatched run {run_id} to host {host_name} ({host_id})")
                await client_gw.broadcast_run_status(run_id, "dispatched")
            else:
                # Dispatch failed - task will be recovered by stuck check
                logger.warning(
                    f"Failed to dispatch run {run_id} to host {host_id}, "
                    f"will be recovered on next cycle"
                )

        # Log summary
        total_actions = (
            len(result.offline_hosts)
            + len(result.requeued_dispatched)
            + len(result.requeued_from_offline)
            + len(result.failed_running)
            + len(result.failed_uploading_offline)
            + len(result.failed_uploading_timeout)
            + len(result.force_canceled)
            + len(result.dispatched)
        )
        if total_actions > 0:
            logger.info(
                f"Reconcile cycle: {len(result.offline_hosts)} hosts offline, "
                f"{len(result.requeued_dispatched) + len(result.requeued_from_offline)} tasks requeued, "
                f"{len(result.failed_running) + len(result.failed_uploading_offline) + len(result.failed_uploading_timeout)} tasks failed, "
                f"{len(result.force_canceled)} tasks force-canceled, "
                f"{len(result.dispatched)} tasks dispatched"
            )


# Global singleton instance
_reconciler: Reconciler | None = None


def get_reconciler() -> Reconciler:
    """Get the global reconciler instance."""
    global _reconciler
    if _reconciler is None:
        _reconciler = Reconciler()
    return _reconciler
