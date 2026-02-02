"""
Secure PATH Construction and Command Resolution

Uses shutil.which() for dynamic command discovery with safety controls.
"""

import os
import shutil
import stat
from pathlib import Path


def build_safe_path(extra: list[str] | None = None) -> str:
    """
    Construct a safe PATH including standard and user installation locations.
    """
    parts = ["/usr/local/bin", "/usr/bin", "/bin"]

    home = Path.home()
    parts += [
        str(home / ".local/bin"),
        str(home / ".cargo/bin"),
        str(home / "go/bin"),
    ]

    if extra:
        parts += extra

    seen = set()
    result = []
    for p in parts:
        if not p or not os.path.isabs(p):
            continue
        if p not in seen:
            seen.add(p)
            result.append(p)

    return ":".join(result)


def resolve_command(command: str, safe_path: str) -> str | None:
    """
    Safely resolve a command to its absolute path.

    Uses shutil.which (no shell), validates file is executable.
    """
    found = shutil.which(command, path=safe_path)
    if not found:
        return None

    try:
        rp = os.path.realpath(found)
        st = os.stat(rp)
    except OSError:
        return None

    if not stat.S_ISREG(st.st_mode):
        return None

    if not (st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
        return None

    return rp
