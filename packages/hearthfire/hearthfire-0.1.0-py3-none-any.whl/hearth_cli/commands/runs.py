import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
from rich.console import Console
from rich.table import Table

from hearth_cli.client import get_client
from hearth_cli.commands.snapshots import (
    _compute_snapshot_id,
    _create_deterministic_tarball,
    _get_storage_mode,
    _upload_rsync,
    _upload_s3,
)

if TYPE_CHECKING:
    from hearth_cli.client import APIClient

app = typer.Typer()
console = Console()


def _upload_snapshot(
    code_path: Path,
    client: "APIClient",
    name: Optional[str] = None,
    host_id: Optional[str] = None,
    excludes: Optional[list[str]] = None,
) -> str:
    """Upload code as snapshot and return snapshot_id.

    Automatically detects storage mode (S3 or rsync) from Controller.

    Args:
        code_path: Path to code directory
        client: API client
        name: Optional snapshot name
        host_id: Optional host ID for rsync target
        excludes: Additional patterns to exclude (fnmatch-style globs)
    """
    code_path = code_path.resolve()

    # Create tarball with extra excludes
    tarball, file_count, excludes_used = _create_deterministic_tarball(code_path, excludes or [])
    snapshot_id = _compute_snapshot_id(tarball)

    console.print(f"[dim]打包: {file_count} 文件, {len(tarball) / 1024:.1f} KB[/dim]")
    if excludes:
        console.print(f"[dim]额外排除: {', '.join(excludes)}[/dim]")

    # Detect storage mode
    storage_mode = _get_storage_mode(client)
    console.print(f"[dim]存储模式: {storage_mode}[/dim]")

    if storage_mode == "rsync":
        # Use rsync upload
        _upload_rsync(client, tarball, snapshot_id, code_path, name, host_id)
    else:
        # Use S3 upload (default)
        _upload_s3(client, tarball, snapshot_id, code_path, name, file_count, excludes_used)

    return snapshot_id


@app.command("submit")
def submit(
    snapshot_id: Optional[str] = typer.Argument(None, help="快照ID（与 --code 二选一）"),
    command: str = typer.Option(..., "--command", "-c", help="执行命令"),
    host: Optional[str] = typer.Option(None, "--host", "-H", help="指定主机ID"),
    gpu: str = typer.Option("any", "--gpu", "-g", help="GPU要求"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="任务名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="任务描述"),
    working_dir: str = typer.Option(".", "--workdir", "-w", help="工作目录"),
    follow: bool = typer.Option(False, "--follow", "-f", help="跟踪日志"),
    code: Optional[Path] = typer.Option(None, "--code", help="代码目录（自动上传为快照）"),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="排除的文件/目录模式 (fnmatch风格, 可重复使用, 如: --exclude '*.log' --exclude 'data/*')",
    ),
) -> None:
    """Submit a run.

    Either provide snapshot_id as argument, or use --code to upload code.

    Examples:
        hearth runs submit sha256:abc... -c "python main.py"
        hearth runs submit --code ./myproject -c "python main.py" -g a100
    """
    # Validate: need either snapshot_id or --code
    if not snapshot_id and not code:
        console.print("[red]错误: 需要提供 snapshot_id 或 --code[/red]")
        raise typer.Exit(1)

    if snapshot_id and code:
        console.print("[red]错误: snapshot_id 和 --code 不能同时使用[/red]")
        raise typer.Exit(1)

    client = get_client()

    # Upload code if --code is provided
    if code:
        if not code.exists():
            console.print(f"[red]错误: 路径不存在: {code}[/red]")
            raise typer.Exit(1)
        if not code.is_dir():
            console.print(f"[red]错误: 路径不是目录: {code}[/red]")
            raise typer.Exit(1)

        with console.status("[bold blue]上传代码...[/bold blue]"):
            snapshot_id = _upload_snapshot(code, client, name, host, exclude or [])

    # Generate client_request_id for idempotency
    client_request_id = str(uuid.uuid4())

    result = client.post(
        "/api/v1/runs",
        {
            "snapshot_id": snapshot_id,
            "command": command,
            "resources": {"gpu": gpu},
            "name": name,
            "description": description,
            "working_dir": working_dir,
            "client_request_id": client_request_id,
            "host_id": host,
        },
    )

    run_id = result["id"]
    console.print(f"任务已创建: {run_id}")

    if follow:
        _follow_logs(run_id)


@app.command("list")
def list_runs(
    status_filter: str = typer.Option(None, "--status", "-s", help="按状态过滤"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量"),
    all_users: bool = typer.Option(False, "--all", "-a", help="显示所有用户的任务"),
    host: Optional[str] = typer.Option(None, "--host", "-H", help="按主机ID过滤"),
) -> None:
    client = get_client()

    params = {"limit": limit, "mine_only": not all_users}
    if status_filter:
        params["status_filter"] = status_filter
    if host:
        params["host_id"] = host

    result = client.get("/api/v1/runs", params=params)
    runs = result.get("runs", [])

    if not runs:
        console.print("[dim]暂无任务[/dim]")
        return

    table = Table(title="任务列表")
    table.add_column("ID", style="cyan")
    table.add_column("名称")
    table.add_column("状态")
    table.add_column("主机")
    table.add_column("创建时间")

    status_colors = {
        "queued": "yellow",
        "dispatched": "blue",
        "running": "cyan",
        "succeeded": "green",
        "failed": "red",
        "canceled": "dim",
    }

    for run in runs:
        status_style = status_colors.get(run["status"], "white")
        # Prefer host_name, fall back to truncated host_id
        host_display = run.get("host_name") or (
            run.get("host_id", "-")[:8] if run.get("host_id") else "-"
        )

        name = run.get("name") or run["command"][:30]
        created = run["created_at"][:19] if run.get("created_at") else "-"

        table.add_row(
            run["id"][:12],
            name,
            f"[{status_style}]{run['status']}[/{status_style}]",
            host_display,
            created,
        )

    console.print(table)


@app.command("status")
def show_status(run_id: str) -> None:
    client = get_client()
    run = client.get(f"/api/v1/runs/{run_id}")

    console.print(f"[bold]任务: {run['id']}[/bold]")
    console.print(f"  状态: {run['status']}")
    console.print(f"  命令: {run['command']}")

    if run.get("host_id"):
        console.print(f"  主机: {run['host_id']}")

    console.print(f"  创建: {run.get('created_at', 'N/A')}")

    if run.get("started_at"):
        console.print(f"  开始: {run['started_at']}")

    if run.get("finished_at"):
        console.print(f"  结束: {run['finished_at']}")

    if run.get("exit_code") is not None:
        console.print(f"  退出码: {run['exit_code']}")

    if run.get("error_message"):
        console.print(f"  [red]错误: {run['error_message']}[/red]")


@app.command("logs")
def show_logs(
    run_id: str,
    limit: int = typer.Option(1000, "--limit", "-n", help="显示行数"),
    follow: bool = typer.Option(False, "--follow", "-f", help="跟踪日志"),
) -> None:
    if follow:
        _follow_logs(run_id)
    else:
        client = get_client()
        result = client.get(f"/api/v1/runs/{run_id}/logs", {"limit": limit})
        console.print(result.get("content", ""), end="")


def _follow_logs(run_id: str) -> None:
    client = get_client()

    console.print("[dim]正在连接日志流...[/dim]")

    try:
        for data in client.stream_get(f"/api/v1/runs/{run_id}/logs/stream"):
            event = json.loads(data)

            if "content" in event:
                console.print(event["content"], end="")
            elif "status" in event:
                console.print()
                console.print(f"[bold]任务结束: {event['status']}[/bold]")
                if event.get("exit_code") is not None:
                    console.print(f"退出码: {event['exit_code']}")
                break
    except KeyboardInterrupt:
        console.print("\n[dim]已停止跟踪[/dim]")


@app.command("cancel")
def cancel(run_id: str) -> None:
    client = get_client()
    client.post(f"/api/v1/runs/{run_id}/cancel")
    console.print(f"任务已取消: {run_id}")


@app.command("retry")
def retry(run_id: str) -> None:
    client = get_client()
    result = client.post(f"/api/v1/runs/{run_id}/retry")
    console.print(f"已重试，新任务ID: {result['id']}")
