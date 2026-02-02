"""Runtime state management for hearth up --detach mode.

Provides utilities for:
- State file management (read/write/remove)
- Process identity verification (via /proc)
- File locking for concurrent start prevention
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from filelock import FileLock, Timeout


def get_state_dir() -> Path:
    """Get the state directory for hearth stacks.

    Uses XDG_RUNTIME_DIR/hearth/stacks if available,
    otherwise falls back to ~/.local/state/hearth/stacks.
    """
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        base = Path(runtime_dir) / "hearth" / "stacks"
    else:
        base = Path.home() / ".local" / "state" / "hearth" / "stacks"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_lock_path(name: str) -> Path:
    """Get the lock file path for a stack name."""
    locks_dir = get_state_dir() / "locks"
    locks_dir.mkdir(parents=True, exist_ok=True)
    return locks_dir / f"{name}.lock"


def acquire_lock(name: str, timeout: float = 0) -> FileLock:
    """Acquire exclusive lock for a stack.

    Args:
        name: Stack name
        timeout: Seconds to wait (0 = non-blocking, raises immediately if locked)

    Returns:
        Acquired FileLock (caller must release/use as context manager)

    Raises:
        Timeout: If lock is already held
    """
    lock_path = get_lock_path(name)
    lock = FileLock(lock_path, timeout=timeout)
    lock.acquire()
    return lock


@dataclass
class ProcIdentity:
    """Process identity for verifying a PID still belongs to expected process."""

    start_time: str  # from /proc/<pid>/stat field 22
    cmdline: list[str]

    def to_dict(self) -> dict:
        return {"start_time": self.start_time, "cmdline": self.cmdline}

    @classmethod
    def from_dict(cls, data: dict) -> ProcIdentity:
        return cls(start_time=data["start_time"], cmdline=data["cmdline"])


@dataclass
class ServiceState:
    """State of a single service process."""

    pid: int
    pgid: int
    argv: list[str]
    ports: dict[str, int]
    log_path: str
    proc_identity: ProcIdentity

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "pgid": self.pgid,
            "argv": self.argv,
            "ports": self.ports,
            "log_path": self.log_path,
            "proc_identity": self.proc_identity.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ServiceState:
        return cls(
            pid=data["pid"],
            pgid=data["pgid"],
            argv=data["argv"],
            ports=data["ports"],
            log_path=data["log_path"],
            proc_identity=ProcIdentity.from_dict(data["proc_identity"]),
        )


@dataclass
class StackState:
    """Full state of a running stack."""

    name: str
    created_at: str  # ISO-8601
    cwd: str
    services: dict[str, ServiceState]
    schema_version: int = 1

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "created_at": self.created_at,
            "cwd": self.cwd,
            "services": {k: v.to_dict() for k, v in self.services.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> StackState:
        return cls(
            schema_version=data.get("schema_version", 1),
            name=data["name"],
            created_at=data["created_at"],
            cwd=data["cwd"],
            services={k: ServiceState.from_dict(v) for k, v in data["services"].items()},
        )


def get_state_path(name: str) -> Path:
    """Get the state file path for a stack name."""
    return get_state_dir() / f"{name}.json"


def read_stack_state(name: str) -> Optional[StackState]:
    """Read and validate state file for a stack.

    Returns None if file doesn't exist or is invalid.
    """
    state_path = get_state_path(name)
    if not state_path.exists():
        return None

    try:
        with open(state_path, "r") as f:
            data = json.load(f)
        return StackState.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def write_stack_state(state: StackState) -> None:
    """Atomic write of state file (tmp + fsync + rename)."""
    state_path = get_state_path(state.name)
    state_dir = state_path.parent
    state_dir.mkdir(parents=True, exist_ok=True)

    # Write to temp file, fsync, then atomic rename
    fd, tmp_path = tempfile.mkstemp(dir=state_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, state_path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def remove_stack_state(name: str) -> None:
    """Remove state file for a stack."""
    state_path = get_state_path(name)
    try:
        state_path.unlink(missing_ok=True)
    except OSError:
        pass


def get_proc_identity(pid: int) -> Optional[ProcIdentity]:
    """Read process identity from /proc.

    Returns None if process doesn't exist or /proc is not available.
    """
    try:
        # Read start_time from /proc/<pid>/stat (field 22, 0-indexed = 21)
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists():
            return None

        with open(stat_path, "r") as f:
            stat_content = f.read()

        # stat format: pid (comm) state ... field22 ...
        # comm can contain spaces/parens, so find the last ')' and parse from there
        last_paren = stat_content.rfind(")")
        if last_paren == -1:
            return None

        fields_after_comm = stat_content[last_paren + 2 :].split()
        # Field 22 in 1-indexed stat = field 20 in 0-indexed fields_after_comm
        # (fields 1-2 are pid and comm, field 3 is state = index 0 in fields_after_comm)
        # Field 22 = starttime = index 19 in fields_after_comm
        if len(fields_after_comm) < 20:
            return None
        start_time = fields_after_comm[19]

        # Read cmdline
        cmdline_path = Path(f"/proc/{pid}/cmdline")
        if not cmdline_path.exists():
            return None

        with open(cmdline_path, "rb") as f:
            cmdline_bytes = f.read()

        # cmdline is null-separated
        cmdline = cmdline_bytes.decode("utf-8", errors="replace").rstrip("\x00").split("\x00")

        return ProcIdentity(start_time=start_time, cmdline=cmdline)

    except (OSError, IOError, IndexError):
        return None


def verify_proc_identity(pid: int, expected: ProcIdentity) -> bool:
    """Check if PID still belongs to the expected process.

    Compares start_time and cmdline prefix to detect PID reuse.
    """
    current = get_proc_identity(pid)
    if current is None:
        return False

    # start_time must match exactly
    if current.start_time != expected.start_time:
        return False

    # cmdline should match (at least the first few elements)
    # We check if expected cmdline is a prefix of current
    if len(current.cmdline) < len(expected.cmdline):
        return False

    for i, arg in enumerate(expected.cmdline):
        if current.cmdline[i] != arg:
            return False

    return True


def get_log_dir(name: str, custom_log_dir: Optional[Path] = None) -> Path:
    """Get the log directory for a stack.

    Uses custom_log_dir if provided, otherwise:
    XDG_STATE_HOME/hearth/logs/<name> or ~/.local/state/hearth/logs/<name>
    """
    if custom_log_dir:
        log_dir = custom_log_dir / name
    else:
        state_home = os.environ.get("XDG_STATE_HOME")
        if state_home:
            log_dir = Path(state_home) / "hearth" / "logs" / name
        else:
            log_dir = Path.home() / ".local" / "state" / "hearth" / "logs" / name

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def create_stack_state(
    name: str,
    services: dict[str, ServiceState],
) -> StackState:
    """Create a new StackState with current timestamp and cwd."""
    return StackState(
        name=name,
        created_at=datetime.now(timezone.utc).isoformat(),
        cwd=str(Path.cwd()),
        services=services,
    )


def list_stack_states() -> list[StackState]:
    """List all saved stack states.

    Scans the state directory for *.json files and returns valid StackState objects.
    Invalid/corrupted files are skipped.
    """
    state_dir = get_state_dir()
    states = []

    for json_file in state_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            state = StackState.from_dict(data)
            states.append(state)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Skip invalid files
            continue

    # Sort by created_at (newest first)
    states.sort(key=lambda s: s.created_at, reverse=True)
    return states
