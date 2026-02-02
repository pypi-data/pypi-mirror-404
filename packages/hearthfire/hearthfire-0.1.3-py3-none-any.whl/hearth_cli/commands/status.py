"""hearth status - show running background services."""

from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from hearth_cli.runtime_state import (
    list_stack_states,
    read_stack_state,
    verify_proc_identity,
)

app = typer.Typer()
console = Console()


def _check_process_status(pid: int, proc_identity) -> str:
    """Check process status and return a status string."""
    try:
        import os

        os.kill(pid, 0)  # Check if process exists
    except OSError:
        return "[red]stopped[/red]"

    # Process exists, check identity
    if verify_proc_identity(pid, proc_identity):
        return "[green]running[/green]"
    else:
        return "[yellow]stale[/yellow]"


def _check_health(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """Check controller health endpoint.

    Returns (success, message).
    """
    try:
        # Disable proxy for local connections
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return True, "[green]healthy[/green]"
            else:
                return False, f"[yellow]HTTP {resp.status_code}[/yellow]"
    except httpx.ConnectError:
        return False, "[red]connection refused[/red]"
    except httpx.TimeoutException:
        return False, "[red]timeout[/red]"
    except Exception as e:
        return False, f"[red]{type(e).__name__}[/red]"


@app.callback(invoke_without_command=True)
def status(
    name: str = typer.Option("default", "--name", "-n", help="服务栈名称"),
    all_stacks: bool = typer.Option(False, "--all", "-a", help="显示所有服务栈"),
    check_health: bool = typer.Option(False, "--check-health", help="检查服务健康状态"),
) -> None:
    """显示后台服务栈状态。

    Examples:
        hearth status                        # 显示 default 栈
        hearth status --name dev             # 显示 dev 栈
        hearth status --all                  # 显示所有栈
    """
    if all_stacks:
        _show_all_stacks()
        return
    # Read stack state
    state = read_stack_state(name)
    if state is None:
        console.print(f"[red]未找到服务栈 '{name}'[/red]")
        console.print(f"[dim]提示: 使用 'hearth up -d --name {name}' 启动服务[/dim]")
        raise typer.Exit(1)

    # Display stack info
    console.print(f"\n[bold]服务栈: {name}[/bold]")
    console.print(f"[dim]创建时间: {state.created_at}[/dim]")
    console.print(f"[dim]工作目录: {state.cwd}[/dim]")

    # Create table for services
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("服务", style="white")
    table.add_column("PID", style="white")
    table.add_column("PGID", style="white")
    table.add_column("状态", style="white")
    table.add_column("端口", style="white")
    table.add_column("日志路径", style="dim")

    # Display order: controller -> webui -> worker
    display_order = ["controller", "webui", "worker"]
    controller_port = None

    for svc_name in display_order:
        if svc_name not in state.services:
            continue

        svc = state.services[svc_name]
        status_str = _check_process_status(svc.pid, svc.proc_identity)

        # Format ports
        if svc.ports:
            ports_str = ", ".join(f"{k}={v}" for k, v in svc.ports.items())
            if svc_name == "controller" and "http" in svc.ports:
                controller_port = svc.ports["http"]
        else:
            ports_str = "-"

        table.add_row(
            svc_name,
            str(svc.pid),
            str(svc.pgid),
            status_str,
            ports_str,
            svc.log_path,
        )

    console.print("")
    console.print(table)

    # Health check if requested
    if check_health:
        console.print("\n[bold]健康检查:[/bold]")

        if controller_port:
            health_url = f"http://localhost:{controller_port}/health"
            console.print(f"  Controller /health ({health_url}): ", end="")
            success, msg = _check_health(health_url)
            console.print(msg)
        else:
            console.print("  [yellow]Controller 端口未知，跳过健康检查[/yellow]")

    console.print("")


def _show_all_stacks() -> None:
    """Show status of all stacks."""
    states = list_stack_states()

    if not states:
        console.print("[yellow]没有运行中的服务栈[/yellow]")
        console.print("[dim]使用 'hearth up -d --name <name>' 启动服务[/dim]")
        return

    table = Table(title="服务栈列表", show_header=True, header_style="bold cyan")
    table.add_column("名称", style="white")
    table.add_column("创建时间", style="dim")
    table.add_column("服务", style="white")
    table.add_column("状态", style="white")

    for state in states:
        # Count running services
        running = 0
        total = len(state.services)
        for svc in state.services.values():
            status_str = _check_process_status(svc.pid, svc.proc_identity)
            if "running" in status_str:
                running += 1

        if running == total:
            status = f"[green]{running}/{total} running[/green]"
        elif running > 0:
            status = f"[yellow]{running}/{total} running[/yellow]"
        else:
            status = f"[red]{running}/{total} running[/red]"

        services = ", ".join(state.services.keys())

        table.add_row(
            state.name,
            state.created_at[:19],  # Truncate microseconds
            services,
            status,
        )

    console.print(table)
    console.print(f"\n[dim]共 {len(states)} 个服务栈[/dim]")
