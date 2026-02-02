import asyncio
import contextlib
import os
import pty
import select
import signal
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_pty_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pty-reader")

_ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "SHELL",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TMPDIR",
        "XDG_RUNTIME_DIR",
    }
)

_SECRET_PREFIXES = ("HEARTH_CONTROLLER_", "HEARTH_STORAGE_")


def _build_task_env(task_env: dict) -> dict:
    base_env = {}
    for key in _ENV_ALLOWLIST:
        if key in os.environ:
            base_env[key] = os.environ[key]

    base_env["PYTHONUNBUFFERED"] = "1"
    base_env["TERM"] = "xterm-256color"
    base_env["COLUMNS"] = "120"
    base_env["LINES"] = "40"

    for key, value in task_env.items():
        if not any(key.startswith(prefix) for prefix in _SECRET_PREFIXES):
            base_env[key] = value

    return base_env


def _is_progress_line(text: str) -> bool:
    """Check if a line looks like a progress bar that should be suppressed.

    Progress bars typically contain:
    - Block characters: ░ █ ▓ ▒
    - Percentage patterns: [X/Y] or XX%
    - Are meant to be overwritten (contain \r)
    """
    # Common progress bar characters
    progress_chars = {"░", "█", "▓", "▒", "━", "─", "■", "□", "●", "○"}
    has_progress_chars = any(c in text for c in progress_chars)

    # Pattern like [1/24] or [08/24]
    import re

    has_counter = bool(re.search(r"\[\s*\d+/\d+\s*\]", text))
    has_percent = bool(re.search(r"\d+%", text))

    return has_progress_chars and (has_counter or has_percent)


def _process_output_with_cr(text: str) -> list[str]:
    """Process output handling carriage returns for progress bars.

    Splits text by newlines, then for each line, if it contains \r,
    only keeps the last segment (simulating terminal overwrite behavior).
    Also filters out intermediate progress bar states.
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        if "\r" in line:
            # Keep only the last segment after \r (terminal overwrites previous content)
            segments = line.split("\r")
            # Filter out empty segments and keep the last non-empty one
            non_empty = [s for s in segments if s.strip()]
            if non_empty:
                final_segment = non_empty[-1]
                # Skip intermediate progress states - only keep if it looks complete
                # A complete progress typically shows 100% or [N/N] where both numbers match
                if _is_progress_line(final_segment):
                    # Check if it's a complete progress (100% or final state)
                    import re

                    match = re.search(r"\[(\d+)/(\d+)\]", final_segment)
                    if match and match.group(1) != match.group(2):
                        # Intermediate state like [8/24], skip it
                        continue
                result.append(final_segment)
        else:
            result.append(line)
    return result


class PTYRunner:
    def __init__(self) -> None:
        self.current_pid: int | None = None
        self._cancelled = False

    async def run(
        self,
        command: str,
        work_dir: Path,
        env: dict,
        on_output: Callable[[str], None],
        timeout: int = 3600,
    ) -> int:
        self._cancelled = False

        master_fd, slave_fd = pty.openpty()

        full_env = _build_task_env(env)

        pid = os.fork()

        if pid == 0:
            os.close(master_fd)
            os.setsid()

            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)

            if slave_fd > 2:
                os.close(slave_fd)

            os.chdir(work_dir)
            os.execvpe("/bin/bash", ["bash", "-c", command], full_env)

        else:
            os.close(slave_fd)
            self.current_pid = pid

            try:
                exit_code = await self._read_output(master_fd, pid, on_output, timeout)
            finally:
                os.close(master_fd)
                self.current_pid = None

            return exit_code
        return None

    async def _read_output(
        self,
        master_fd: int,
        pid: int,
        on_output: Callable[[str], None],
        timeout: int,
    ) -> int:
        loop = asyncio.get_event_loop()
        start_time = loop.time()
        buffer = b""

        def blocking_select(fd: int, timeout_sec: float) -> bool:
            ready, _, _ = select.select([fd], [], [], timeout_sec)
            return bool(ready)

        def blocking_read(fd: int) -> bytes:
            return os.read(fd, 4096)

        while True:
            if loop.time() - start_time > timeout:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                await asyncio.sleep(1)
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                with contextlib.suppress(ChildProcessError):
                    os.waitpid(pid, os.WNOHANG)
                return -1

            if self._cancelled:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    await asyncio.sleep(1)
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                with contextlib.suppress(ChildProcessError):
                    os.waitpid(pid, os.WNOHANG)
                return -2

            ready = await loop.run_in_executor(_pty_executor, blocking_select, master_fd, 0.1)

            if ready:
                try:
                    data = await loop.run_in_executor(_pty_executor, blocking_read, master_fd)
                    if data:
                        buffer += data
                        if b"\n" in buffer or len(buffer) > 1024:
                            text = buffer.decode("utf-8", errors="replace")
                            processed_lines = _process_output_with_cr(text)
                            for line in processed_lines:
                                if line:
                                    on_output(line)
                            buffer = b""
                    else:
                        break
                except OSError:
                    break

            pid_result, status = os.waitpid(pid, os.WNOHANG)
            if pid_result != 0:
                while True:
                    try:
                        data = await loop.run_in_executor(_pty_executor, blocking_read, master_fd)
                        if data:
                            text = data.decode("utf-8", errors="replace")
                            processed_lines = _process_output_with_cr(text)
                            for line in processed_lines:
                                if line:
                                    on_output(line)
                        else:
                            break
                    except OSError:
                        break

                if buffer:
                    text = buffer.decode("utf-8", errors="replace")
                    on_output(text)

                if os.WIFEXITED(status):
                    return os.WEXITSTATUS(status)
                if os.WIFSIGNALED(status):
                    return -os.WTERMSIG(status)
                return -1

            await asyncio.sleep(0.01)

        if buffer:
            text = buffer.decode("utf-8", errors="replace")
            on_output(text)

        # Process exited via break (EOF on pty), get actual exit status
        try:
            _, status = os.waitpid(pid, 0)
            if os.WIFEXITED(status):
                return os.WEXITSTATUS(status)
            if os.WIFSIGNALED(status):
                return -os.WTERMSIG(status)
        except ChildProcessError:
            pass
        return -1

    def cancel(self) -> None:
        self._cancelled = True
        if self.current_pid:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(os.getpgid(self.current_pid), signal.SIGTERM)
