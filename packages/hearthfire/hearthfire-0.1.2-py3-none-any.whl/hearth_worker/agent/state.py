from dataclasses import dataclass, field

import psutil

try:
    import pynvml

    pynvml.nvmlInit()
    HAS_NVIDIA = True
except Exception:
    HAS_NVIDIA = False


@dataclass
class GPUInfo:
    name: str
    uuid: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_percent: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "uuid": self.uuid,
            "memory_total_mb": self.memory_total_mb,
            "memory_used_mb": self.memory_used_mb,
            "utilization_percent": self.utilization_percent,
        }


@dataclass
class WorkerState:
    worker_id: str
    status: str = "online"

    cpu_percent: float = 0
    memory_total_gb: float = 0
    memory_used_gb: float = 0
    disk_total_gb: float = 0
    disk_used_gb: float = 0

    gpus: list[GPUInfo] = field(default_factory=list)

    current_task_id: str | None = None
    current_attempt_id: str | None = None

    cached_snapshots: list[str] = field(default_factory=list)

    def refresh(self) -> None:
        self.cpu_percent = psutil.cpu_percent(interval=None)

        mem = psutil.virtual_memory()
        self.memory_total_gb = mem.total / (1024**3)
        self.memory_used_gb = mem.used / (1024**3)

        disk = psutil.disk_usage("/")
        self.disk_total_gb = disk.total / (1024**3)
        self.disk_used_gb = disk.used / (1024**3)

        self.gpus = self._get_gpu_info()

    def _get_gpu_info(self) -> list[GPUInfo]:
        if not HAS_NVIDIA:
            return []

        gpus = []
        try:
            device_count = pynvml.nvmlDeviceGetCount()

            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                uuid = pynvml.nvmlDeviceGetUUID(handle)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)

                gpus.append(
                    GPUInfo(
                        name=name if isinstance(name, str) else name.decode(),
                        uuid=uuid if isinstance(uuid, str) else uuid.decode(),
                        memory_total_mb=memory.total // (1024 * 1024),
                        memory_used_mb=memory.used // (1024 * 1024),
                        utilization_percent=util.gpu,
                    )
                )
        except Exception:
            pass

        return gpus
