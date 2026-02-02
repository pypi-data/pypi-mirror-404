import asyncio
import os
import sys
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

from hearth_worker.config import settings
from hearth_worker.executor.pty_runner import PTYRunner

if TYPE_CHECKING:
    from hearth_worker.agent.session import WorkerSession
    from hearth_worker.cache.store import SnapshotCache
    from hearth_worker.spool.queue import SpoolQueue
    from hearth_worker.storage.client import StorageClient

LOG_QUEUE_MAX_SIZE = 100
LOG_SEND_TIMEOUT = 5.0


def _safe_extract_tar(tar: tarfile.TarFile, dest_dir: Path) -> None:
    dest_dir = dest_dir.resolve()

    for member in tar.getmembers():
        if os.path.isabs(member.name):
            raise ValueError(f"Absolute path in tar: {member.name}")

        target_path = (dest_dir / member.name).resolve()

        try:
            target_path.relative_to(dest_dir)
        except ValueError:
            raise ValueError(f"Path traversal attempt: {member.name}")

        if member.issym() or member.islnk():
            if member.issym():
                link_target = os.path.normpath(
                    os.path.join(os.path.dirname(target_path), member.linkname)
                )
            else:
                link_target = (dest_dir / member.linkname).resolve()

            link_target = Path(link_target).resolve()
            try:
                link_target.relative_to(dest_dir)
            except ValueError:
                raise ValueError(f"Symlink escape attempt: {member.name} -> {member.linkname}")

    # Python 3.12+ provides native safe extraction via filter='data' which:
    # - Strips absolute paths and parent directory references
    # - Rejects symlinks/hardlinks escaping the destination
    # - Sets restrictive permissions
    # For older versions, we rely on the manual validation above.
    if sys.version_info >= (3, 12):
        tar.extractall(dest_dir, filter="data")
    else:
        tar.extractall(dest_dir)


def _validate_working_dir(base_dir: Path, working_dir: str) -> Path:
    if not working_dir or working_dir == ".":
        return base_dir

    if os.path.isabs(working_dir):
        raise ValueError(f"Absolute working_dir not allowed: {working_dir}")

    target = (base_dir / working_dir).resolve()
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError(f"working_dir escapes base directory: {working_dir}")

    return target


class TaskExecutor:
    def __init__(
        self,
        cache: "SnapshotCache",
        storage: "StorageClient | None",
        spool: "SpoolQueue",
        session: "WorkerSession",
    ):
        self.cache = cache
        self.storage = storage
        self.spool = spool
        self.session = session
        self.pty_runner = PTYRunner()

        self.runs_dir = Path(settings.runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, task: dict) -> int:
        run_id = task["run_id"]
        attempt_id = task["attempt_id"]
        snapshot_id = task["snapshot_id"]
        command = task["command"]
        working_dir = task.get("working_dir", ".")
        env = task.get("env", {})
        timeout = task.get("timeout_seconds", 3600)

        await self.session.send_task_accepted(run_id, attempt_id)

        work_dir = self.runs_dir / run_id / attempt_id

        try:
            snapshot_path = await self._fetch_snapshot(run_id, snapshot_id, attempt_id)

            work_dir = await self._prepare_work_dir(run_id, attempt_id, snapshot_path, working_dir)

            await self.session.send_task_started(run_id, attempt_id, str(work_dir))

            log_queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=LOG_QUEUE_MAX_SIZE)
            dropped_count = 0
            sender_task = asyncio.create_task(self._log_sender(run_id, attempt_id, log_queue))

            def enqueue_log(text: str) -> None:
                nonlocal dropped_count
                try:
                    log_queue.put_nowait(text)
                except asyncio.QueueFull:
                    dropped_count += 1

            try:
                exit_code = await self.pty_runner.run(
                    command=command,
                    work_dir=work_dir,
                    env=env,
                    on_output=enqueue_log,
                    timeout=timeout,
                )
            finally:
                try:
                    log_queue.put_nowait(None)
                except asyncio.QueueFull:
                    sender_task.cancel()
                try:
                    await asyncio.wait_for(sender_task, timeout=LOG_SEND_TIMEOUT)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

                if dropped_count > 0:
                    try:
                        await self.session.send_task_log(
                            run_id,
                            attempt_id,
                            f"\n[hearth] Warning: {dropped_count} log chunks dropped due to buffer full\n",
                        )
                    except Exception:
                        pass

            await self.session.send_task_uploading(run_id, attempt_id)
            try:
                await self._collect_results(run_id, attempt_id, work_dir)
            except Exception as upload_error:
                await self.session.send_task_failed(
                    run_id, attempt_id, "upload_error", f"Failed to collect results: {upload_error}"
                )
                return -1

            if exit_code >= 0:
                await self.session.send_task_completed(run_id, attempt_id, exit_code)
            elif exit_code == -2:
                await self.session.send_task_canceled(run_id, attempt_id, exit_code)
            else:
                await self.session.send_task_failed(
                    run_id, attempt_id, "process_error", f"Exit code: {exit_code}"
                )

            return exit_code

        except Exception as e:
            await self.session.send_task_failed(run_id, attempt_id, "execution_error", str(e))
            return -1

    async def _fetch_snapshot(self, run_id: str, snapshot_id: str, attempt_id: str) -> Path:
        cached = self.cache.get(snapshot_id)
        if cached:
            await self.session.send_task_log(
                run_id, attempt_id, f"[hearth] Using cached snapshot {snapshot_id[:12]}\n"
            )
            return cached

        if not self.storage:
            raise RuntimeError("Storage not configured and snapshot not cached")

        await self.session.send_task_log(
            run_id, attempt_id, f"[hearth] Downloading snapshot {snapshot_id[:12]}...\n"
        )

        data = await self.storage.download(f"snapshots/{snapshot_id}/code.tar.gz")
        snapshot_path = await self.cache.store(snapshot_id, data)

        await self.session.send_task_log(
            run_id, attempt_id, f"[hearth] Snapshot downloaded ({len(data) / 1024 / 1024:.1f} MB)\n"
        )

        return snapshot_path

    async def _prepare_work_dir(
        self, run_id: str, attempt_id: str, snapshot_path: Path, working_dir: str
    ) -> Path:
        work_dir = self.runs_dir / run_id / attempt_id
        work_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(snapshot_path, "r:gz") as tar:
            _safe_extract_tar(tar, work_dir)

        return _validate_working_dir(work_dir, working_dir)

    async def _collect_results(self, run_id: str, attempt_id: str, work_dir: Path) -> None:
        outputs_dir = work_dir / "outputs"
        if not outputs_dir.exists():
            return

        for file_path in outputs_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(outputs_dir)

                try:
                    if self.storage:
                        await self.storage.upload(
                            f"results/{run_id}/{attempt_id}/{rel_path}",
                            file_path.read_bytes(),
                        )
                except Exception:
                    await self.spool.enqueue(
                        run_id=run_id,
                        attempt_id=attempt_id,
                        path=str(rel_path),
                        data=file_path.read_bytes(),
                    )

    async def _log_sender(
        self, run_id: str, attempt_id: str, queue: "asyncio.Queue[str | None]"
    ) -> None:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            try:
                await self.session.send_task_log(run_id, attempt_id, chunk)
            except Exception:
                pass

    def cancel(self, run_id: str) -> None:  # noqa: ARG002
        self.pty_runner.cancel()
