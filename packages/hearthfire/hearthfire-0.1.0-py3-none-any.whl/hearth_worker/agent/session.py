import asyncio
from typing import TYPE_CHECKING

from hearth_worker.config import settings

if TYPE_CHECKING:
    from hearth_worker.agent.connection import ConnectionManager
    from hearth_worker.agent.state import WorkerState


class WorkerSession:
    def __init__(self, connection: "ConnectionManager", state: "WorkerState"):
        self.connection = connection
        self.state = state

    async def start_heartbeat(self) -> None:
        """Start heartbeat loop using controller-negotiated interval."""
        while True:
            await self._send_heartbeat()
            # Read interval dynamically from connection (set after WELCOME)
            interval = self.connection.heartbeat_interval or 30
            await asyncio.sleep(interval)

    async def _send_heartbeat(self) -> None:
        self.state.refresh()
        heartbeat = {
            "type": "heartbeat",
            "payload": {
                "worker_id": self.state.worker_id,
                "status": self.state.status,
                "cpu_percent": self.state.cpu_percent,
                "memory_used_gb": self.state.memory_used_gb,
                "memory_total_gb": self.state.memory_total_gb,
                "disk_used_gb": self.state.disk_used_gb,
                "disk_total_gb": self.state.disk_total_gb,
                "gpus": [gpu.to_dict() for gpu in self.state.gpus],
                "current_task_id": self.state.current_task_id,
                "current_attempt_id": self.state.current_attempt_id,
                "cached_snapshots": self.state.cached_snapshots,
                # SSH config for rsync fallback
                "ssh_host": settings.get_ssh_host(),
                "ssh_port": settings.ssh_port,
                "ssh_user": settings.get_ssh_user(),
                "snapshot_inbox_path": settings.snapshot_inbox_path,
                "api_port": settings.api_port,
            },
        }
        await self.connection.send(heartbeat)

    async def send_task_accepted(self, run_id: str, attempt_id: str) -> None:
        await self.connection.send(
            {
                "type": "task_accepted",
                "payload": {"run_id": run_id, "attempt_id": attempt_id},
                "run_id": run_id,
            }
        )

    async def send_task_started(self, run_id: str, attempt_id: str, work_path: str) -> None:
        await self.connection.send(
            {
                "type": "task_started",
                "payload": {
                    "run_id": run_id,
                    "attempt_id": attempt_id,
                    "work_path": work_path,
                },
                "run_id": run_id,
            }
        )

    async def send_task_uploading(self, run_id: str, attempt_id: str) -> None:
        await self.connection.send(
            {
                "type": "task_uploading",
                "payload": {"run_id": run_id, "attempt_id": attempt_id},
                "run_id": run_id,
            }
        )

    async def send_task_log(
        self, run_id: str, attempt_id: str, content: str, stream: str = "stdout"
    ) -> None:
        await self.connection.send(
            {
                "type": "task_log",
                "payload": {
                    "run_id": run_id,
                    "attempt_id": attempt_id,
                    "stream_id": "main",
                    "chunk_index": 0,
                    "content": content,
                    "stream": stream,
                },
                "run_id": run_id,
            }
        )

    async def send_task_completed(self, run_id: str, attempt_id: str, exit_code: int) -> None:
        await self.connection.send(
            {
                "type": "task_completed",
                "payload": {
                    "run_id": run_id,
                    "attempt_id": attempt_id,
                    "exit_code": exit_code,
                },
                "run_id": run_id,
            }
        )

    async def send_task_failed(
        self, run_id: str, attempt_id: str, error_type: str, error_message: str
    ) -> None:
        await self.connection.send(
            {
                "type": "task_failed",
                "payload": {
                    "run_id": run_id,
                    "attempt_id": attempt_id,
                    "error_type": error_type,
                    "error_message": error_message,
                },
                "run_id": run_id,
            }
        )

    async def send_task_canceled(self, run_id: str, attempt_id: str, exit_code: int) -> None:
        await self.connection.send(
            {
                "type": "task_canceled",
                "payload": {"run_id": run_id, "attempt_id": attempt_id, "exit_code": exit_code},
                "run_id": run_id,
            }
        )
