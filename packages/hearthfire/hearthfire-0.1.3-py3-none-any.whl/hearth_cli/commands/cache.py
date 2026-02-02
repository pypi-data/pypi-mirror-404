"""Cache management commands for hearth CLI.

Provides utilities for:
- Listing cache types, paths, sizes, and file counts
- Cleaning cache directories with dry-run support
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(no_args_is_help=True)


class CacheType(str, Enum):
    WORKER_SNAPSHOTS = "worker-snapshots"
    CLI_LOGS = "cli-logs"
    CLI_STATE = "cli-state"
    ALL = "all"


@dataclass
class CacheInfo:
    """Information about a cache directory."""

    cache_type: CacheType
    path: Path
    size_bytes: int
    file_count: int
    exists: bool

    def size_human(self) -> str:
        """Return human-readable size (KB/MB/GB)."""
        size = self.size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


def _get_worker_cache_dir() -> Path:
    """Get worker snapshot cache directory from config or default."""
    # Use same default as worker config
    cache_dir = os.environ.get("HEARTH_CACHE_DIR", "~/.hearth/worker/cache")
    return Path(cache_dir).expanduser()


def _get_cli_state_dir() -> Path:
    """Get CLI state directory (XDG_RUNTIME_DIR or fallback)."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "hearth" / "stacks"
    return Path.home() / ".local" / "state" / "hearth" / "stacks"


def _get_cli_log_dir() -> Path:
    """Get CLI log directory (XDG_STATE_HOME or fallback)."""
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "hearth" / "logs"
    return Path.home() / ".local" / "state" / "hearth" / "logs"


def _calculate_dir_stats(path: Path, pattern: str = "*") -> tuple[int, int]:
    """Calculate total size and file count for a directory.

    Args:
        path: Directory path
        pattern: Glob pattern for files to count

    Returns:
        Tuple of (total_size_bytes, file_count)
    """
    if not path.exists():
        return 0, 0

    total_size = 0
    file_count = 0

    try:
        for item in path.rglob(pattern):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass

    return total_size, file_count


def _get_cache_info(cache_type: CacheType) -> CacheInfo:
    """Get information about a specific cache type."""
    if cache_type == CacheType.WORKER_SNAPSHOTS:
        path = _get_worker_cache_dir()
        size, count = _calculate_dir_stats(path, "*.tar.gz")
    elif cache_type == CacheType.CLI_LOGS:
        path = _get_cli_log_dir()
        size, count = _calculate_dir_stats(path)
    elif cache_type == CacheType.CLI_STATE:
        path = _get_cli_state_dir()
        size, count = _calculate_dir_stats(path, "*.json")
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")

    return CacheInfo(
        cache_type=cache_type,
        path=path,
        size_bytes=size,
        file_count=count,
        exists=path.exists(),
    )


def _get_all_cache_info() -> list[CacheInfo]:
    """Get information about all cache types."""
    return [
        _get_cache_info(CacheType.WORKER_SNAPSHOTS),
        _get_cache_info(CacheType.CLI_LOGS),
        _get_cache_info(CacheType.CLI_STATE),
    ]


def _format_path(path: Path, max_width: int = 40) -> str:
    """Format path with ~ for home directory, truncate if needed."""
    home = str(Path.home())
    path_str = str(path)
    if path_str.startswith(home):
        path_str = "~" + path_str[len(home) :]

    if len(path_str) > max_width:
        path_str = "..." + path_str[-(max_width - 3) :]

    return path_str


def _delete_cache_files(cache_type: CacheType, dry_run: bool = True) -> tuple[int, int]:
    """Delete files from a cache directory.

    Args:
        cache_type: Type of cache to clean
        dry_run: If True, only report what would be deleted

    Returns:
        Tuple of (files_deleted, bytes_freed)
    """
    info = _get_cache_info(cache_type)
    if not info.exists:
        return 0, 0

    files_deleted = 0
    bytes_freed = 0

    if cache_type == CacheType.WORKER_SNAPSHOTS:
        pattern = "*.tar.gz"
        for item in info.path.glob(pattern):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    if not dry_run:
                        item.unlink()
                    files_deleted += 1
                    bytes_freed += size
                except (OSError, PermissionError) as e:
                    if not dry_run:
                        typer.secho(f"  Failed to delete {item}: {e}", fg=typer.colors.YELLOW)

    elif cache_type == CacheType.CLI_LOGS:
        # Delete all log directories and files
        for item in info.path.iterdir():
            if item.is_dir():
                try:
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    count = sum(1 for f in item.rglob("*") if f.is_file())
                    if not dry_run:
                        shutil.rmtree(item)
                    files_deleted += count
                    bytes_freed += size
                except (OSError, PermissionError) as e:
                    if not dry_run:
                        typer.secho(f"  Failed to delete {item}: {e}", fg=typer.colors.YELLOW)
            elif item.is_file():
                try:
                    size = item.stat().st_size
                    if not dry_run:
                        item.unlink()
                    files_deleted += 1
                    bytes_freed += size
                except (OSError, PermissionError) as e:
                    if not dry_run:
                        typer.secho(f"  Failed to delete {item}: {e}", fg=typer.colors.YELLOW)

    elif cache_type == CacheType.CLI_STATE:
        # Delete state JSON files (not lock files - those are ephemeral)
        for item in info.path.glob("*.json"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    if not dry_run:
                        item.unlink()
                    files_deleted += 1
                    bytes_freed += size
                except (OSError, PermissionError) as e:
                    if not dry_run:
                        typer.secho(f"  Failed to delete {item}: {e}", fg=typer.colors.YELLOW)
        # Also clean locks directory
        locks_dir = info.path / "locks"
        if locks_dir.exists():
            for item in locks_dir.glob("*.lock"):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                        if not dry_run:
                            item.unlink()
                        files_deleted += 1
                        bytes_freed += size
                    except (OSError, PermissionError) as e:
                        if not dry_run:
                            typer.secho(f"  Failed to delete {item}: {e}", fg=typer.colors.YELLOW)

    return files_deleted, bytes_freed


def _size_human(size_bytes: int) -> str:
    """Return human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@app.command("list")
def cache_list() -> None:
    """List all cache types with paths, sizes, and file counts."""
    caches = _get_all_cache_info()

    typer.echo("\nCache Summary:\n")
    typer.echo(f"{'Type':<20} {'Path':<45} {'Size':>10} {'Files':>8}")
    typer.echo("─" * 85)

    total_size = 0
    for cache in caches:
        path_str = _format_path(cache.path, 43)
        size_str = cache.size_human() if cache.exists else "-"
        count_str = str(cache.file_count) if cache.exists else "-"

        typer.echo(f"{cache.cache_type.value:<20} {path_str:<45} {size_str:>10} {count_str:>8}")
        total_size += cache.size_bytes

    typer.echo("─" * 85)
    typer.echo(f"\nTotal: {_size_human(total_size)}")
    typer.echo()
    typer.secho(
        "[info] worker-spool and worker-runs are not included (potentially active data)",
        fg=typer.colors.CYAN,
    )


@app.command("clean")
def cache_clean(
    cache_type: CacheType = typer.Option(
        ...,
        "--type",
        "-t",
        help="Cache type to clean (worker-snapshots, cli-logs, cli-state, all)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Actually perform deletion (without this, only shows what would be deleted)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be deleted without deleting (default if --yes not specified)",
    ),
) -> None:
    """Clean cache directories.

    By default (without --yes), shows what would be deleted.
    Use --yes/-y to actually perform the deletion.

    Safe cache types (included in 'all'):
    - worker-snapshots: Cached snapshot archives
    - cli-logs: CLI service log files
    - cli-state: CLI state files for detached services

    NOT included by default (use specific type):
    - worker-spool: May have pending uploads (dangerous)
    - worker-runs: May have active run data (dangerous)
    """
    # If neither --yes nor --dry-run specified, default to dry-run behavior
    actual_dry_run = not yes or dry_run

    if cache_type == CacheType.ALL:
        types_to_clean = [CacheType.WORKER_SNAPSHOTS, CacheType.CLI_LOGS, CacheType.CLI_STATE]
    else:
        types_to_clean = [cache_type]

    if actual_dry_run:
        typer.secho("\n[DRY RUN] The following would be deleted:\n", fg=typer.colors.YELLOW)
    else:
        typer.echo("\nCleaning caches...\n")

    total_files = 0
    total_bytes = 0

    for ct in types_to_clean:
        info = _get_cache_info(ct)
        if not info.exists:
            typer.echo(f"  {ct.value}: (not found)")
            continue

        files, size = _delete_cache_files(ct, dry_run=actual_dry_run)
        total_files += files
        total_bytes += size

        if files > 0:
            action = "would delete" if actual_dry_run else "deleted"
            typer.echo(f"  {ct.value}: {action} {files} files ({_size_human(size)})")
        else:
            typer.echo(f"  {ct.value}: (empty)")

    typer.echo()
    if actual_dry_run:
        typer.secho(
            f"Total: {total_files} files ({_size_human(total_bytes)}) would be deleted",
            fg=typer.colors.YELLOW,
        )
        typer.echo()
        typer.secho("Run with --yes to actually delete these files.", fg=typer.colors.CYAN)
    else:
        typer.secho(
            f"Cleaned: {total_files} files ({_size_human(total_bytes)}) deleted",
            fg=typer.colors.GREEN,
        )
