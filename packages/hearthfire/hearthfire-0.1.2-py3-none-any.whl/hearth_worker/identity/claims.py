"""
Machine Claims Collection

Collects machine identification information for host registration.
"""

import socket
from pathlib import Path


def collect_claims() -> dict:
    """
    Collect machine identification claims.

    Returns:
        Dict with hostname, machine_id, dmi_uuid (if available), and dmi_uuid_error (if read failed)
    """
    dmi_uuid, dmi_uuid_error = _read_dmi_uuid()
    return {
        "hostname": _get_hostname(),
        "machine_id": _read_machine_id(),
        "dmi_uuid": dmi_uuid,
        "dmi_uuid_error": dmi_uuid_error,
    }


def _get_hostname() -> str:
    """Get the machine hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _read_machine_id() -> str | None:
    """
    Read /etc/machine-id.

    This is a unique, stable identifier generated at OS install time.
    """
    try:
        return Path("/etc/machine-id").read_text().strip()
    except Exception:
        return None


def _read_dmi_uuid() -> tuple[str | None, str | None]:
    """
    Read DMI product UUID from sysfs.

    This is a hardware-based UUID, stable across OS reinstalls.
    Requires root or appropriate permissions.

    Returns:
        Tuple of (value, error_reason). If successful, error_reason is None.
        If failed, value is None and error_reason describes the failure.
    """
    dmi_path = Path("/sys/class/dmi/id/product_uuid")
    try:
        return (dmi_path.read_text().strip(), None)
    except PermissionError:
        return (None, "permission_denied")
    except FileNotFoundError:
        return (None, "file_not_found")
    except OSError as e:
        return (None, f"os_error:{e.errno}")


def collect_hardware() -> dict:
    """
    Collect basic hardware information.

    Returns:
        Dict with cpu_cores, memory_gb, etc.
    """
    import os

    result = {}

    # CPU cores
    try:
        result["cpu_cores"] = os.cpu_count() or 0
    except Exception:
        pass

    # Memory (from /proc/meminfo)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    # MemTotal is in kB
                    kb = int(line.split()[1])
                    result["memory_gb"] = round(kb / (1024 * 1024), 1)
                    break
    except Exception:
        pass

    # Disk space (root partition)
    try:
        statvfs = os.statvfs("/")
        total_bytes = statvfs.f_blocks * statvfs.f_frsize
        result["disk_gb"] = round(total_bytes / (1024**3), 1)
    except Exception:
        pass

    # GPU detection (nvidia-smi)
    gpu_info = _detect_nvidia_gpu()
    if gpu_info:
        result.update(gpu_info)

    return result


def _detect_nvidia_gpu() -> dict | None:
    """
    Detect NVIDIA GPU using nvidia-smi.

    Returns:
        Dict with gpu_name, gpu_vram_gb, gpu_count or None if no GPU
    """
    import shutil
    import subprocess

    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None

    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        lines = result.stdout.strip().split("\n")
        if not lines:
            return None

        parts = [p.strip() for p in lines[0].split(",")]
        if len(parts) >= 2:
            gpu_name = parts[0]
            try:
                memory_mib = int(parts[1])
                gpu_vram_gb = round(memory_mib / 1024, 1)
            except ValueError:
                gpu_vram_gb = None

            return {
                "gpu_name": gpu_name,
                "gpu_vram_gb": gpu_vram_gb,
                "gpu_count": len(lines),
            }
    except Exception:
        pass

    return None
