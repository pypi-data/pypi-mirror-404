import asyncio
import contextlib
from enum import Enum

from hearth_controller.storage.client import StorageClient
from hearth_controller.ws.gateway import gateway


class StorageStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class StorageCoordinator:
    def __init__(self, storage: StorageClient | None = None, check_interval: int = 30):
        self.storage = storage
        self.status = StorageStatus.HEALTHY if storage else StorageStatus.UNAVAILABLE
        self._check_interval = check_interval
        self._unhealthy_count = 0
        self._healthy_count = 0
        self._healthy_threshold = 3

    async def start(self) -> None:
        if not self.storage:
            return

        while True:
            await self._check_storage()
            await asyncio.sleep(self._check_interval)

    async def _check_storage(self) -> None:
        if not self.storage:
            return

        is_healthy = await self.storage.health_check()

        if is_healthy:
            self._unhealthy_count = 0
            self._healthy_count += 1
            if (
                self.status != StorageStatus.HEALTHY
                and self._healthy_count >= self._healthy_threshold
            ):
                await self._transition_to_healthy()
        else:
            self._healthy_count = 0
            self._unhealthy_count += 1
            if self._unhealthy_count >= 3:
                await self._transition_to_degraded()

    async def _transition_to_healthy(self) -> None:
        self.status = StorageStatus.HEALTHY

        for _worker_id, conn in gateway.connections.items():
            with contextlib.suppress(Exception):
                await conn.send(
                    "storage_status",
                    {"status": "healthy", "drain_spool": True},
                )

    async def _transition_to_degraded(self) -> None:
        self.status = StorageStatus.DEGRADED

        for _worker_id, conn in gateway.connections.items():
            with contextlib.suppress(Exception):
                await conn.send("storage_status", {"status": "degraded"})

    def can_schedule_task(self, snapshot_id: str, cached_snapshots: list[str]) -> bool:
        if self.status == StorageStatus.HEALTHY:
            return True

        return snapshot_id in cached_snapshots

    def get_status(self) -> dict:
        return {
            "status": self.status.value,
            "unhealthy_count": self._unhealthy_count,
        }


coordinator = StorageCoordinator()
