import asyncio
import logging
import time
from pathlib import Path

import uvicorn

from hearth_worker.agent.connection import ConnectionManager
from hearth_worker.agent.session import WorkerSession
from hearth_worker.agent.state import WorkerState
from hearth_worker.api.server import app as http_app
from hearth_worker.api.server import set_cache
from hearth_worker.cache.store import SnapshotCache
from hearth_worker.config import settings
from hearth_worker.executor.task_executor import TaskExecutor
from hearth_worker.identity import IdentityManager
from hearth_worker.spool.queue import SpoolQueue
from hearth_worker.storage.client import S3StorageClient

logger = logging.getLogger(__name__)


class HearthAgent:
    def __init__(self, config_path: str | None = None):
        if config_path:
            self._load_config(config_path)

        # Initialize identity manager
        self.identity = IdentityManager(settings.identity_dir)
        self.identity.ensure_identity()

        # Worker ID comes from saved host_id or will be assigned by controller
        self.worker_id = self.identity.get_host_id() or "pending"

        self.state = WorkerState(worker_id=self.worker_id)

        self.cache = SnapshotCache(
            cache_dir=Path(settings.cache_dir),
            max_size_gb=settings.cache_max_size_gb,
        )

        self.spool = SpoolQueue(
            spool_dir=Path(settings.spool_dir),
            max_size_gb=settings.spool_max_size_gb,
        )

        self.storage: S3StorageClient | None = None
        if settings.storage_endpoint:
            self.storage = S3StorageClient()

        self.connection = ConnectionManager(
            controller_url=settings.controller_url,
            identity_manager=self.identity,
            on_message=self._handle_message,
        )

        self.session = WorkerSession(self.connection, self.state)

        self.executor = TaskExecutor(
            cache=self.cache,
            storage=self.storage,
            spool=self.spool,
            session=self.session,
        )

        self.state.cached_snapshots = self.cache.list_snapshots()
        self._background_tasks: set[asyncio.Task] = set()
        self._task_semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)

        # Initialize inbox directory for rsync uploads
        inbox_path = Path(settings.snapshot_inbox_path)
        inbox_path.mkdir(parents=True, exist_ok=True)

        # Inject cache into HTTP server module
        set_cache(self.cache)

    def _load_config(self, config_path: str) -> None:
        import os

        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        if host := config.get("host"):
            os.environ.setdefault("HEARTH_WORKER_ID", host.get("id", ""))
            os.environ.setdefault("HEARTH_WORKER_NAME", host.get("name", ""))

        if controller := config.get("controller"):
            os.environ.setdefault("HEARTH_CONTROLLER_URL", controller.get("url", ""))
            os.environ.setdefault("HEARTH_CONTROLLER_TOKEN", controller.get("token", ""))

        if storage := config.get("storage"):
            os.environ.setdefault("HEARTH_STORAGE_ENDPOINT", storage.get("endpoint", ""))
            os.environ.setdefault("HEARTH_STORAGE_ACCESS_KEY", storage.get("access_key", ""))
            os.environ.setdefault("HEARTH_STORAGE_SECRET_KEY", storage.get("secret_key", ""))
            os.environ.setdefault("HEARTH_STORAGE_BUCKET", storage.get("bucket", "hearth"))

        if cache := config.get("cache"):
            os.environ.setdefault("HEARTH_CACHE_DIR", cache.get("dir", ""))
            if max_size := cache.get("max_size_gb"):
                os.environ.setdefault("HEARTH_CACHE_MAX_SIZE_GB", str(max_size))

        if spool := config.get("spool"):
            os.environ.setdefault("HEARTH_SPOOL_DIR", spool.get("dir", ""))
            if max_size := spool.get("max_size_gb"):
                os.environ.setdefault("HEARTH_SPOOL_MAX_SIZE_GB", str(max_size))

    async def run(self) -> None:
        logger.info(f"Starting Hearth Agent: {self.worker_id}")
        logger.info(f"HTTP API listening on {settings.api_host}:{settings.api_port}")

        config = uvicorn.Config(
            http_app,
            host=settings.api_host,
            port=settings.api_port,
            log_level="warning",
        )
        http_server = uvicorn.Server(config)

        tasks = [
            asyncio.create_task(self.connection.run()),
            asyncio.create_task(self.session.start_heartbeat()),
            asyncio.create_task(self._state_refresh_loop()),
            asyncio.create_task(self._spool_drain_loop()),
            asyncio.create_task(self._inbox_cleanup_loop()),
            asyncio.create_task(http_server.serve()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Agent shutting down...")

    async def _handle_message(self, message: dict) -> None:
        msg_type = message.get("type")
        payload = message.get("payload", {})

        if msg_type == "dispatch_task":
            task = asyncio.create_task(self._handle_dispatch_with_limit(payload))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        elif msg_type == "cancel_task":
            self._handle_cancel_task(payload)

    async def _handle_dispatch_with_limit(self, payload: dict) -> None:
        async with self._task_semaphore:
            await self._handle_dispatch_task(payload)

    async def _handle_dispatch_task(self, payload: dict) -> None:
        run_id = payload["run_id"]
        attempt_id = payload.get("attempt_id")

        # Dedupe: ignore if already executing this exact (run_id, attempt_id)
        if self.state.current_task_id == run_id:
            if self.state.current_attempt_id == attempt_id:
                logger.warning(f"Ignoring duplicate dispatch for run {run_id} attempt {attempt_id}")
                return
            else:
                # Same run but different attempt - at-most-once violation
                logger.error(
                    f"Received dispatch for run {run_id} with different attempt_id "
                    f"(current: {self.state.current_attempt_id}, new: {attempt_id}). "
                    f"Ignoring to preserve at-most-once semantics."
                )
                return

        # Dedupe: check if we recently completed this attempt (network retry after completion)
        if (
            hasattr(self, "_completed_attempts")
            and (
                run_id,
                attempt_id,
            )
            in self._completed_attempts
        ):
            logger.warning(
                f"Ignoring dispatch for already-completed attempt: run {run_id} attempt {attempt_id}"
            )
            return

        self.state.current_task_id = run_id
        self.state.current_attempt_id = attempt_id

        try:
            await self.executor.execute(payload)
        finally:
            # Track completed attempt for dedupe (keep last 100)
            if not hasattr(self, "_completed_attempts"):
                self._completed_attempts: set[tuple[str, str | None]] = set()
            self._completed_attempts.add((run_id, attempt_id))
            # Limit size to prevent memory leak
            if len(self._completed_attempts) > 100:
                self._completed_attempts.pop()

            self.state.current_task_id = None
            self.state.current_attempt_id = None

    def _handle_cancel_task(self, payload: dict) -> None:
        run_id = payload["run_id"]
        attempt_id = payload.get("attempt_id")

        if self.state.current_task_id != run_id:
            return

        # If attempt_id provided, verify it matches current attempt (at-most-once)
        if attempt_id is not None and attempt_id != self.state.current_attempt_id:
            logger.warning(
                f"Ignoring cancel for run {run_id}: attempt_id mismatch "
                f"(cancel: {attempt_id}, current: {self.state.current_attempt_id})"
            )
            return

        self.executor.cancel(run_id)

    async def _state_refresh_loop(self) -> None:
        while True:
            self.state.refresh()
            # 刷新 cached_snapshots 列表（包括 rsync 新上传的 snapshots）
            self.state.cached_snapshots = self.cache.list_snapshots()
            await asyncio.sleep(10)

    async def _spool_drain_loop(self) -> None:
        while True:
            try:
                if self.storage:
                    await self.spool.drain(self.storage)
            except Exception as e:
                logger.error(f"Spool drain error: {e}")
            await asyncio.sleep(60)

    async def _inbox_cleanup_loop(self) -> None:
        """Clean up stale inbox files (older than 10 minutes)."""
        inbox_ttl_seconds = 600  # 10 minutes
        cleanup_interval = 300  # Check every 5 minutes

        while True:
            await asyncio.sleep(cleanup_interval)
            try:
                inbox = Path(settings.snapshot_inbox_path)
                if not inbox.exists():
                    continue
                cutoff = time.time() - inbox_ttl_seconds
                for f in inbox.iterdir():
                    if f.is_file() and f.stat().st_mtime < cutoff:
                        try:
                            f.unlink()
                            logger.info(f"Cleaned up stale inbox file: {f.name}")
                        except OSError as e:
                            logger.warning(f"Failed to delete stale inbox file {f}: {e}")
            except Exception as e:
                logger.warning(f"Inbox cleanup error: {e}")
