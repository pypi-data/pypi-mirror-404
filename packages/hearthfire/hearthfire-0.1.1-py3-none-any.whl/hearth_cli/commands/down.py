"""hearth down - stop running background services."""

import os
import signal
import time
from typing import Optional

import typer
from rich.console import Console

from hearth_cli.runtime_state import (
    list_stack_states,
    read_stack_state,
    remove_stack_state,
    verify_proc_identity,
)

app = typer.Typer()
console = Console()


def _process_exists(pid: int) -> bool:
    """Check if a process exists."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _kill_service(
    name: str,
    pid: int,
    pgid: int,
    proc_identity,
    force: bool,
    timeout: int,
) -> tuple[bool, str]:
    """Kill a single service by PGID.

    Returns (success, message).
    """
    # Verify process identity first
    if not verify_proc_identity(pid, proc_identity):
        if not force:
            return False, f"PID {pid} 身份不匹配 (进程已重用)，跳过"
        # Force mode: kill anyway if process exists
        if not _process_exists(pid):
            return True, f"进程 {pid} 不存在"

    try:
        # Send SIGTERM to process group
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return True, f"进程组 {pgid} 不存在"
    except PermissionError:
        return False, f"无权限终止进程组 {pgid}"
    except OSError as e:
        return False, f"发送 SIGTERM 失败: {e}"

    # Wait for graceful shutdown
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not _process_exists(pid):
            return True, "已停止"
        time.sleep(0.2)

    # Still running after timeout
    if force:
        try:
            os.killpg(pgid, signal.SIGKILL)
            time.sleep(0.5)
            if not _process_exists(pid):
                return True, "已强制终止 (SIGKILL)"
            return False, "SIGKILL 后仍在运行"
        except ProcessLookupError:
            return True, "已停止"
        except OSError as e:
            return False, f"SIGKILL 失败: {e}"
    else:
        return False, f"超时 ({timeout}s)，使用 --force 强制终止"


@app.callback(invoke_without_command=True)
def down(
    name: str = typer.Option("default", "--name", "-n", help="服务栈名称"),
    all_stacks: bool = typer.Option(False, "--all", "-a", help="停止所有服务栈"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认提示"),
    only: Optional[str] = typer.Option(
        None, "--only", help="仅停止指定服务 (controller/webui/worker)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="强制停止 (SIGKILL)"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="等待优雅停止的秒数"),
) -> None:
    """停止后台运行的服务栈。

    Examples:
        hearth down --name dev            # 停止 dev 栈所有服务
        hearth down --name dev --only controller  # 仅停止 controller
        hearth down --name dev --force    # 强制终止
        hearth down --all                 # 停止所有栈 (需确认)
        hearth down --all --yes           # 停止所有栈 (无需确认)
    """
    if all_stacks:
        _stop_all_stacks(yes, force, timeout)
        return
    # Read stack state
    state = read_stack_state(name)
    if state is None:
        console.print(f"[red]未找到服务栈 '{name}'[/red]")
        raise typer.Exit(1)

    # Validate --only if provided
    if only:
        valid_services = {"controller", "webui", "worker"}
        if only not in valid_services:
            console.print(f"[red]无效的服务名 '{only}'，可选: {', '.join(valid_services)}[/red]")
            raise typer.Exit(1)
        if only not in state.services:
            console.print(f"[red]服务 '{only}' 不在栈 '{name}' 中[/red]")
            console.print(f"[dim]可用服务: {', '.join(state.services.keys())}[/dim]")
            raise typer.Exit(1)

    # Determine services to stop (reverse order: worker -> webui -> controller)
    stop_order = ["worker", "webui", "controller"]
    if only:
        services_to_stop = [only]
    else:
        services_to_stop = [s for s in stop_order if s in state.services]

    console.print(f"[blue]正在停止服务栈 '{name}'...[/blue]")

    # Track results
    success_count = 0
    fail_count = 0

    for svc_name in services_to_stop:
        svc = state.services[svc_name]
        console.print(f"\n[yellow]停止 {svc_name} (PID={svc.pid}, PGID={svc.pgid})...[/yellow]")

        success, msg = _kill_service(
            svc_name,
            svc.pid,
            svc.pgid,
            svc.proc_identity,
            force,
            timeout,
        )

        if success:
            console.print(f"  [green]✓ {msg}[/green]")
            success_count += 1
        else:
            console.print(f"  [red]✗ {msg}[/red]")
            fail_count += 1

    # Summary
    console.print("")
    if fail_count == 0:
        console.print(f"[green]✓ 所有服务已停止 ({success_count} 个)[/green]")
        # Remove state file only on complete success
        if not only:
            remove_stack_state(name)
            console.print(f"[dim]状态文件已清理[/dim]")
    else:
        console.print(f"[yellow]部分服务停止失败: {success_count} 成功, {fail_count} 失败[/yellow]")
        console.print(f"[dim]状态文件保留，请手动检查进程[/dim]")
        raise typer.Exit(1)


def _stop_all_stacks(yes: bool, force: bool, timeout: int) -> None:
    """Stop all stacks."""
    states = list_stack_states()

    if not states:
        console.print("[yellow]没有运行中的服务栈[/yellow]")
        return

    # Show what will be stopped
    console.print(f"[yellow]将停止以下 {len(states)} 个服务栈:[/yellow]")
    for state in states:
        console.print(f"  - {state.name} ({', '.join(state.services.keys())})")

    # Confirm unless --yes
    if not yes:
        confirm = typer.confirm("确定要停止所有服务栈吗?")
        if not confirm:
            console.print("[dim]已取消[/dim]")
            raise typer.Exit(0)

    # Stop each stack
    total_success = 0
    total_fail = 0

    for state in states:
        console.print(f"\n[blue]停止服务栈 '{state.name}'...[/blue]")

        # Stop services in reverse order: worker -> webui -> controller
        stop_order = ["worker", "webui", "controller"]
        services_to_stop = [s for s in stop_order if s in state.services]

        stack_success = 0
        stack_fail = 0

        for svc_name in services_to_stop:
            svc = state.services[svc_name]
            console.print(f"  [yellow]停止 {svc_name} (PID={svc.pid})...[/yellow]")

            success, msg = _kill_service(
                svc_name,
                svc.pid,
                svc.pgid,
                svc.proc_identity,
                force,
                timeout,
            )

            if success:
                console.print(f"    [green]✓ {msg}[/green]")
                stack_success += 1
            else:
                console.print(f"    [red]✗ {msg}[/red]")
                stack_fail += 1

        if stack_fail == 0:
            remove_stack_state(state.name)
            total_success += 1
        else:
            total_fail += 1

    # Summary
    console.print("")
    if total_fail == 0:
        console.print(f"[green]✓ 所有服务栈已停止 ({total_success} 个)[/green]")
    else:
        console.print(
            f"[yellow]部分服务栈停止失败: {total_success} 成功, {total_fail} 失败[/yellow]"
        )
        raise typer.Exit(1)
