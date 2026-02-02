"""Snapshot management commands."""

import gzip
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import httpx
import typer
from rich.console import Console

from hearth_cli.client import get_client

if TYPE_CHECKING:
    from hearth_cli.client import APIClient

app = typer.Typer()
console = Console()

# Patterns to exclude from snapshot (same as server)
EXCLUDE_PATTERNS = [
    ".git",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "env",
    "venv",
    ".venv",
    ".env",
    "node_modules",
    ".npm",
    ".yarn",
    "*.egg-info",
    "dist",
    "build",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
    "Thumbs.db",
    "*.log",
    "*.swp",
    "*.swo",
]


def _should_exclude(
    path: Path, base_path: Path, exclude_patterns: Optional[set[str]] = None
) -> bool:
    """Check if a path should be excluded from the snapshot.

    Args:
        path: Path to check
        base_path: Base path for relative path calculation
        exclude_patterns: Custom patterns to use (defaults to EXCLUDE_PATTERNS)
    """
    import fnmatch as fnmatch_mod

    patterns = exclude_patterns if exclude_patterns is not None else set(EXCLUDE_PATTERNS)
    rel_path = path.relative_to(base_path)

    for part in rel_path.parts:
        for pattern in patterns:
            if pattern.startswith("*"):
                # Suffix match like *.pyc
                if part.endswith(pattern[1:]):
                    return True
            elif part == pattern:
                # Exact match
                return True
            elif fnmatch_mod.fnmatch(part, pattern):
                # Full fnmatch pattern match
                return True

    # Also check full relative path for patterns like "data/*"
    rel_path_str = str(rel_path)
    for pattern in patterns:
        if fnmatch_mod.fnmatch(rel_path_str, pattern):
            return True

    return False


def _get_git_info(code_path: Path) -> dict[str, Any]:
    """Get git information if available."""
    import subprocess

    git_info = {}
    git_dir = code_path / ".git"

    if not git_dir.exists():
        return git_info

    try:
        # Get current commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=code_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            git_info["git_commit"] = result.stdout.strip()

        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=code_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            git_info["git_branch"] = result.stdout.strip()

        # Get remote URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=code_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            git_info["git_repo"] = result.stdout.strip()

        # Check if dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=code_path,
            capture_output=True,
            text=True,
        )
        git_info["git_dirty"] = bool(result.stdout.strip())

    except FileNotFoundError:
        pass  # git not installed

    return git_info


def _create_deterministic_tarball(
    code_path: Path,
    extra_excludes: Optional[list[str]] = None,
) -> tuple[bytes, int, list[str]]:
    """Create a deterministic tar.gz of the code directory.

    Args:
        code_path: Path to code directory
        extra_excludes: Additional patterns to exclude (fnmatch-style globs)

    Returns:
        Tuple of (tarball_bytes, file_count, excludes_used).
    """
    code_path = code_path.resolve()

    # Merge default and user excludes
    all_excludes = set(EXCLUDE_PATTERNS)
    if extra_excludes:
        all_excludes.update(extra_excludes)

    # Collect files (sorted for determinism)
    files: list[Path] = []
    for root, dirs, filenames in os.walk(code_path):
        root_path = Path(root)

        # Filter directories in-place
        dirs[:] = [d for d in dirs if not _should_exclude(root_path / d, code_path, all_excludes)]

        for filename in filenames:
            file_path = root_path / filename
            if not _should_exclude(file_path, code_path, all_excludes):
                files.append(file_path)

    files.sort()

    # Create tarball in memory
    tar_buffer = io.BytesIO()

    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        for file_path in files:
            arcname = str(file_path.relative_to(code_path))

            # Create TarInfo with normalized fields for determinism
            info = tar.gettarinfo(file_path, arcname=arcname)
            info.mtime = 0  # Reset modification time
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""

            with open(file_path, "rb") as f:
                tar.addfile(info, f)

    tar_bytes = tar_buffer.getvalue()

    # Compress with gzip (mtime=0 for determinism)
    gz_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=gz_buffer, mode="wb", mtime=0) as gz:
        gz.write(tar_bytes)

    return gz_buffer.getvalue(), len(files), sorted(all_excludes)


def _compute_snapshot_id(tarball: bytes) -> str:
    """Compute snapshot ID as sha256 hash of tarball."""
    hash_hex = hashlib.sha256(tarball).hexdigest()
    return f"sha256:{hash_hex}"


def _get_storage_mode(client: "APIClient") -> str:
    """Get Controller's storage mode."""
    result = client.get("/api/v1/storage/mode")
    return result.get("mode", "s3")


def _upload_s3(
    client: "APIClient",
    tarball: bytes,
    snapshot_id: str,
    code_path: Path,
    name: Optional[str],
    file_count: int,
    excludes: Optional[list[str]] = None,
) -> None:
    """Upload snapshot using S3 presigned URLs.

    Args:
        client: API client
        tarball: Tarball bytes
        snapshot_id: Snapshot ID
        code_path: Path to code directory
        name: Optional snapshot name
        file_count: Number of files in tarball
        excludes: List of exclude patterns used (for manifest)
    """
    # Prepare upload
    prepare_resp = client.post(
        "/api/v1/snapshots/prepare",
        {
            "snapshot_id": snapshot_id,
            "size_bytes": len(tarball),
            "name": name,
        },
    )

    if prepare_resp.get("already_exists"):
        console.print("[green]✓ 快照已存在，跳过上传[/green]")
        console.print(f"[bold]snapshot_id: {snapshot_id}[/bold]")
        return

    code_upload_url = prepare_resp["code_upload_url"]
    manifest_upload_url = prepare_resp["manifest_upload_url"]

    # Upload tarball directly to storage
    with console.status("[bold blue]上传代码...[/bold blue]"):
        with httpx.Client(timeout=300.0) as http:
            resp = http.put(
                code_upload_url,
                content=tarball,
                headers={"Content-Type": "application/gzip"},
            )
            if resp.status_code >= 400:
                console.print(f"[red]上传失败: {resp.status_code} {resp.text}[/red]")
                raise typer.Exit(1)

    console.print("  [dim]代码已上传[/dim]")

    # Create and upload manifest
    git_info = _get_git_info(code_path)
    manifest = {
        "snapshot_id": snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": git_info,
        "content": {
            "size_bytes": len(tarball),
            "file_count": file_count,
            "excludes": excludes if excludes is not None else EXCLUDE_PATTERNS,
        },
    }

    with console.status("[bold blue]上传元数据...[/bold blue]"):
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        with httpx.Client(timeout=30.0) as http:
            resp = http.put(
                manifest_upload_url,
                content=manifest_bytes,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                console.print(f"[red]元数据上传失败: {resp.status_code}[/red]")
                raise typer.Exit(1)

    console.print("  [dim]元数据已上传[/dim]")

    # Confirm upload
    with console.status("[bold blue]确认注册...[/bold blue]"):
        confirm_resp = client.post(
            "/api/v1/snapshots/confirm",
            {
                "snapshot_id": snapshot_id,
                "name": name or code_path.name,
                "size_bytes": len(tarball),
                "manifest": manifest,
            },
        )

    if confirm_resp.get("created"):
        console.print("[green]✓ 快照创建成功[/green]")
    else:
        console.print("[green]✓ 快照已确认[/green]")

    console.print(f"[bold]snapshot_id: {snapshot_id}[/bold]")


def _upload_rsync(
    client: "APIClient",
    tarball: bytes,
    snapshot_id: str,
    code_path: Path,
    name: Optional[str],
    host_id: Optional[str] = None,
) -> None:
    """Upload snapshot using rsync to Worker's inbox."""
    size_bytes = len(tarball)

    # 1. Call prepare-rsync API
    console.print(f"[blue]准备 rsync 上传 {snapshot_id[:20]}...[/blue]")
    prepare_resp = client.post(
        "/api/v1/snapshots/prepare-rsync",
        {"snapshot_id": snapshot_id, "size_bytes": size_bytes, "host_id": host_id},
    )

    if prepare_resp.get("already_exists"):
        console.print("[green]✓ 快照已存在，跳过上传[/green]")
        console.print(f"[bold]snapshot_id: {snapshot_id}[/bold]")
        return

    ticket = prepare_resp["ticket"]
    ssh_user = prepare_resp["ssh_user"]
    ssh_host = prepare_resp["ssh_host"]
    ssh_port = prepare_resp["ssh_port"]
    inbox_path = prepare_resp["inbox_path"]

    # 2. Write tarball to temp file
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as f:
        f.write(tarball)
        tarball_path = Path(f.name)

    try:
        # 3. Build rsync command with Hearth's managed known_hosts
        # File name uses {ticket}.tar.gz so Worker can identify it
        from hearth_cli.commands.hosts import get_known_hosts_path

        known_hosts = get_known_hosts_path()

        # Check if known_hosts exists - if not, give helpful error
        if not known_hosts.exists():
            console.print(
                f"[red]SSH host not trusted. Run: hearth hosts trust {host_id or '<host>'}[/red]"
            )
            console.print(
                "[dim]This fetches and stores the host's SSH key for secure uploads.[/dim]"
            )
            raise typer.Exit(1)

        # Build SSH options with Hearth's known_hosts and strict checking
        ssh_opts = (
            f"ssh -p {ssh_port} -o UserKnownHostsFile={known_hosts} -o StrictHostKeyChecking=yes"
        )

        remote_path = f"{ssh_user}@{ssh_host}:{inbox_path}/{ticket}.tar.gz"
        rsync_cmd = [
            "rsync",
            "-avz",
            "--progress",
            "-e",
            ssh_opts,
            str(tarball_path),
            remote_path,
        ]

        console.print(f"[blue]通过 rsync 上传到 {ssh_host}...[/blue]")
        console.print(f"[dim]命令: {' '.join(rsync_cmd)}[/dim]")

        # 4. Execute rsync (allow interactive password input)
        # Note: Don't capture stdin to let user enter password
        result = subprocess.run(rsync_cmd)

        if result.returncode != 0:
            console.print(f"[red]rsync 失败，退出码: {result.returncode}[/red]")
            raise typer.Exit(1)

    finally:
        # Clean up temp file
        tarball_path.unlink(missing_ok=True)

    # 5. Call confirm-rsync API
    console.print("[blue]确认上传...[/blue]")
    client.post(
        "/api/v1/snapshots/confirm-rsync",
        {"snapshot_id": snapshot_id, "ticket": ticket},
    )

    console.print(f"[green]✓ 快照 {snapshot_id[:20]}... 上传成功![/green]")
    console.print(f"[bold]snapshot_id: {snapshot_id}[/bold]")


@app.command("upload")
def upload(
    code_path: Path = typer.Argument(..., help="代码目录路径"),
    name: str = typer.Option(None, "--name", "-n", help="快照名称"),
    mode: str = typer.Option(None, "--mode", "-m", help="强制存储模式: s3 或 rsync"),
) -> None:
    """Upload code directory as a snapshot.

    Creates a tarball of the code, uploads directly to storage,
    and registers the snapshot with the controller.

    Automatically detects storage mode (S3 or rsync) from Controller.
    Use --mode to force a specific mode.
    """
    if not code_path.exists():
        console.print(f"[red]错误: 路径不存在: {code_path}[/red]")
        raise typer.Exit(1)

    if not code_path.is_dir():
        console.print(f"[red]错误: 路径不是目录: {code_path}[/red]")
        raise typer.Exit(1)

    if mode and mode not in ("s3", "rsync"):
        console.print(f"[red]错误: 无效的存储模式: {mode}，必须是 s3 或 rsync[/red]")
        raise typer.Exit(1)

    code_path = code_path.resolve()
    console.print(f"[dim]打包目录: {code_path}[/dim]")

    # Step 1: Create tarball
    with console.status("[bold blue]打包代码...[/bold blue]"):
        tarball, file_count, excludes_used = _create_deterministic_tarball(code_path)
        snapshot_id = _compute_snapshot_id(tarball)

    console.print(f"  文件数: {file_count}")
    console.print(f"  大小: {len(tarball) / 1024:.1f} KB")
    console.print(f"  ID: {snapshot_id}")

    client = get_client()

    # Step 2: Determine storage mode
    if mode:
        storage_mode = mode
        console.print(f"[dim]强制使用存储模式: {storage_mode}[/dim]")
    else:
        storage_mode = _get_storage_mode(client)
        console.print(f"[dim]检测到存储模式: {storage_mode}[/dim]")

    # Step 3: Upload based on mode
    if storage_mode == "s3":
        _upload_s3(client, tarball, snapshot_id, code_path, name, file_count, excludes_used)
    elif storage_mode == "rsync":
        _upload_rsync(client, tarball, snapshot_id, code_path, name)
    else:
        console.print(f"[red]错误: 未知存储模式: {storage_mode}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_snapshot(snapshot_id: str = typer.Argument(..., help="快照ID")) -> None:
    """Get snapshot metadata."""
    client = get_client()

    try:
        snapshot = client.get(f"/api/v1/snapshots/{snapshot_id}")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]快照: {snapshot['id']}[/bold]")
    console.print(f"  名称: {snapshot.get('name', '-')}")
    console.print(f"  大小: {snapshot.get('size_bytes', 0) / 1024:.1f} KB")
    console.print(f"  来源: {snapshot.get('source_type', '-')}")

    if snapshot.get("git_commit"):
        console.print(f"  Git: {snapshot.get('git_branch', '')} @ {snapshot['git_commit'][:8]}")

    console.print(f"  创建: {snapshot.get('created_at', '-')}")
    console.print(f"  最后使用: {snapshot.get('last_used_at', '-')}")
