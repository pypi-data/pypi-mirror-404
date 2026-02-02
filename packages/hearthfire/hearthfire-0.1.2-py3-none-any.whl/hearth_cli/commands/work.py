"""hearth work - worker lifecycle management commands.

Provides subcommands for:
- up: Start worker in foreground or background
- down: Stop background worker
- status: Show worker process status
- logs: View worker logs
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
from filelock import Timeout
from rich.console import Console

from hearth_cli.runtime_state import (
    ProcIdentity,
    ServiceState,
    acquire_lock,
    create_stack_state,
    get_log_dir,
    get_proc_identity,
    read_stack_state,
    remove_stack_state,
    verify_proc_identity,
    write_stack_state,
)

app = typer.Typer(help="Worker 生命周期管理")
console = Console()

# Default worker HTTP port for health checks
DEFAULT_WORKER_PORT = 43111
# Stack name prefix to avoid collision with controller stacks
WORKER_STACK_PREFIX = "worker-"


def _get_worker_stack_name(name: str) -> str:
    """Get full stack name with worker prefix."""
    return f"{WORKER_STACK_PREFIX}{name}"


def _wait_for_health(url: str, timeout: float = 10.0) -> bool:
    """Poll health URL until it returns 200 or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = httpx.get(url, timeout=1.0, trust_env=False)
            if resp.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return False


def _start_worker_foreground(
    controller_url: str,
    worker_port: int,
    config_path: Optional[Path],
) -> subprocess.Popen:
    """Start worker in foreground mode."""
    env = os.environ.copy()
    env["HEARTH_CONTROLLER_URL"] = controller_url
    env["HEARTH_WORKER_PORT"] = str(worker_port)
    if config_path:
        env["HEARTH_CONFIG"] = str(config_path)

    cmd = [sys.executable, "-m", "hearth_worker"]
    console.print(f"[blue]启动 Worker (前台模式)[/blue]")
    console.print(f"[dim]命令: {' '.join(cmd)}[/dim]")
    console.print(f"[dim]HEARTH_CONTROLLER_URL={controller_url}[/dim]")

    proc = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env,
    )
    return proc


def _start_worker_detached(
    controller_url: str,
    worker_port: int,
    config_path: Optional[Path],
    log_dir: Path,
) -> tuple[subprocess.Popen, ServiceState]:
    """Start worker in detached mode with logging."""
    log_path = log_dir / "worker.log"

    env = os.environ.copy()
    env["HEARTH_CONTROLLER_URL"] = controller_url
    env["HEARTH_WORKER_PORT"] = str(worker_port)
    if config_path:
        env["HEARTH_CONFIG"] = str(config_path)

    cmd = [sys.executable, "-m", "hearth_worker"]

    # Open log file
    log_file = open(log_path, "w")

    # Start process in new session (detached)
    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )

    # Get process group ID
    pgid = os.getpgid(proc.pid)

    # Get process identity for later verification
    proc_identity = get_proc_identity(proc.pid)
    if proc_identity is None:
        proc_identity = ProcIdentity(start_time="0", cmdline=cmd)

    service_state = ServiceState(
        pid=proc.pid,
        pgid=pgid,
        argv=cmd,
        ports={"http": worker_port},
        log_path=str(log_path),
        proc_identity=proc_identity,
    )

    return proc, service_state


def _process_exists(pid: int) -> bool:
    """Check if a process exists."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _kill_worker(
    pid: int,
    pgid: int,
    proc_identity: ProcIdentity,
    force: bool,
    timeout: int,
) -> tuple[bool, str]:
    """Kill worker process by PGID.

    Returns (success, message).
    """
    # Verify process identity first
    if not verify_proc_identity(pid, proc_identity):
        if not force:
            return False, f"PID {pid} 身份不匹配 (进程已重用)，跳过"
        if not _process_exists(pid):
            return True, f"进程 {pid} 不存在"

    try:
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


def _check_process_status(pid: int, proc_identity: ProcIdentity) -> str:
    """Check process status and return a status string."""
    try:
        os.kill(pid, 0)
    except OSError:
        return "[red]stopped[/red]"

    if verify_proc_identity(pid, proc_identity):
        return "[green]running[/green]"
    else:
        return "[yellow]stale[/yellow]"


def _check_health(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """Check worker health endpoint."""
    try:
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


@app.command()
def up(
    detach: bool = typer.Option(
        False,
        "--detach",
        "-d",
        help="后台模式运行，立即返回",
    ),
    name: str = typer.Option(
        "default",
        "--name",
        "-n",
        help="Worker 实例名称",
    ),
    controller_url: str = typer.Option(
        None,
        "--controller-url",
        "-c",
        envvar="HEARTH_CONTROLLER_URL",
        help="Controller WebSocket URL (默认: ws://localhost:43110)",
    ),
    worker_port: int = typer.Option(
        DEFAULT_WORKER_PORT,
        "--port",
        "-p",
        help="Worker HTTP 端口 (健康检查)",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Worker 配置文件路径",
    ),
    log_dir: Optional[Path] = typer.Option(
        None,
        "--log-dir",
        help="日志目录 (默认: ~/.local/state/hearth/logs/worker-<name>)",
    ),
) -> None:
    """启动 Worker。

    Examples:
        hearth work up                        # 前台启动
        hearth work up -d --name gpu1         # 后台启动，名为 gpu1
        hearth work up -c ws://server:43110   # 指定 Controller URL
    """
    # Default controller URL
    if controller_url is None:
        controller_url = "ws://localhost:43110"

    if detach:
        # Background mode
        stack_name = _get_worker_stack_name(name)
        stack_log_dir = get_log_dir(stack_name, log_dir)

        # Try to acquire lock
        try:
            lock = acquire_lock(stack_name, timeout=0)
        except Timeout:
            existing_state = read_stack_state(stack_name)
            if existing_state:
                for svc_name, svc in existing_state.services.items():
                    if verify_proc_identity(svc.pid, svc.proc_identity):
                        console.print(f"[red]错误: Worker '{name}' 已在运行 (PID={svc.pid})[/red]")
                        raise typer.Exit(1)
                # Stale state, clean up
                remove_stack_state(stack_name)
                try:
                    lock = acquire_lock(stack_name, timeout=0)
                except Timeout:
                    console.print(f"[red]错误: 无法获取锁 '{stack_name}'[/red]")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]错误: 无法获取锁 '{stack_name}'[/red]")
                raise typer.Exit(1)

        try:
            stack_log_dir.mkdir(parents=True, exist_ok=True)

            console.print(f"[blue]启动 Worker: {name}[/blue]")
            console.print(f"[dim]Controller URL: {controller_url}[/dim]")

            proc, service_state = _start_worker_detached(
                controller_url, worker_port, config_path, stack_log_dir
            )

            # Brief check that process started
            time.sleep(0.5)
            if proc.poll() is not None:
                console.print(f"[red]错误: Worker 启动失败，退出码: {proc.returncode}[/red]")
                console.print(f"[dim]查看日志: {stack_log_dir / 'worker.log'}[/dim]")
                lock.release()
                raise typer.Exit(1)

            # Poll for health
            health_url = f"http://localhost:{worker_port}/health"
            console.print(f"[dim]等待 Worker 就绪 (polling {health_url})...[/dim]")
            if _wait_for_health(health_url, timeout=15.0):
                console.print("[green]Worker 已就绪[/green]")
            else:
                console.print("[yellow]警告: 健康检查超时，Worker 可能仍在启动中[/yellow]")

            # Write state
            stack_state = create_stack_state(stack_name, {"worker": service_state})
            write_stack_state(stack_state)

            console.print(f"\n[green]✓ Worker 已在后台启动 (name={name})[/green]")
            console.print(f"[dim]日志: {stack_log_dir / 'worker.log'}[/dim]")
            console.print(f"[dim]使用 'hearth work down --name {name}' 停止[/dim]")

        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            lock.release()
            raise typer.Exit(1)
        finally:
            lock.release()

    else:
        # Foreground mode
        console.print(f"[blue]启动 Worker (前台模式)[/blue]")
        console.print(f"[dim]Controller URL: {controller_url}[/dim]")
        console.print(f"[dim]按 Ctrl+C 终止[/dim]\n")

        proc = _start_worker_foreground(controller_url, worker_port, config_path)

        try:
            proc.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]收到中断信号，正在停止 Worker...[/yellow]")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        exit_code = proc.returncode
        if exit_code != 0:
            console.print(f"[red]Worker 退出，退出码: {exit_code}[/red]")
            raise typer.Exit(exit_code)
        console.print("[green]Worker 已停止[/green]")


@app.command()
def down(
    name: str = typer.Option("default", "--name", "-n", help="Worker 实例名称"),
    force: bool = typer.Option(False, "--force", "-f", help="强制停止 (SIGKILL)"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="等待优雅停止的秒数"),
) -> None:
    """停止后台运行的 Worker。

    Examples:
        hearth work down --name gpu1          # 停止名为 gpu1 的 Worker
        hearth work down --name gpu1 --force  # 强制终止
    """
    stack_name = _get_worker_stack_name(name)

    state = read_stack_state(stack_name)
    if state is None:
        console.print(f"[red]未找到 Worker '{name}'[/red]")
        console.print(f"[dim]提示: 使用 'hearth work up -d --name {name}' 启动[/dim]")
        raise typer.Exit(1)

    if "worker" not in state.services:
        console.print(f"[red]状态文件中未找到 worker 服务[/red]")
        raise typer.Exit(1)

    svc = state.services["worker"]
    console.print(f"[blue]正在停止 Worker '{name}' (PID={svc.pid}, PGID={svc.pgid})...[/blue]")

    success, msg = _kill_worker(
        svc.pid,
        svc.pgid,
        svc.proc_identity,
        force,
        timeout,
    )

    if success:
        console.print(f"[green]✓ {msg}[/green]")
        remove_stack_state(stack_name)
        console.print(f"[dim]状态文件已清理[/dim]")
    else:
        console.print(f"[red]✗ {msg}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    name: str = typer.Option("default", "--name", "-n", help="Worker 实例名称"),
    check_health: bool = typer.Option(False, "--check-health", help="检查健康状态"),
) -> None:
    """显示 Worker 状态。

    Examples:
        hearth work status --name gpu1
        hearth work status --name gpu1 --check-health
    """
    stack_name = _get_worker_stack_name(name)

    state = read_stack_state(stack_name)
    if state is None:
        console.print(f"[red]未找到 Worker '{name}'[/red]")
        console.print(f"[dim]提示: 使用 'hearth work up -d --name {name}' 启动[/dim]")
        raise typer.Exit(1)

    if "worker" not in state.services:
        console.print(f"[red]状态文件中未找到 worker 服务[/red]")
        raise typer.Exit(1)

    svc = state.services["worker"]

    console.print(f"\n[bold]Worker: {name}[/bold]")
    console.print(f"[dim]创建时间: {state.created_at}[/dim]")
    console.print(f"[dim]工作目录: {state.cwd}[/dim]")

    status_str = _check_process_status(svc.pid, svc.proc_identity)
    worker_port = svc.ports.get("http", DEFAULT_WORKER_PORT)

    console.print(f"\n  PID:    {svc.pid}")
    console.print(f"  PGID:   {svc.pgid}")
    console.print(f"  状态:   {status_str}")
    console.print(f"  端口:   {worker_port}")
    console.print(f"  日志:   {svc.log_path}")

    if check_health:
        health_url = f"http://localhost:{worker_port}/health"
        console.print(f"\n[bold]健康检查:[/bold]")
        console.print(f"  /health ({health_url}): ", end="")
        _, msg = _check_health(health_url)
        console.print(msg)

    console.print("")


@app.command()
def logs(
    name: str = typer.Option("default", "--name", "-n", help="Worker 实例名称"),
    follow: bool = typer.Option(False, "--follow", "-f", help="实时跟踪日志"),
    tail: int = typer.Option(50, "--tail", help="显示最后 N 行"),
) -> None:
    """查看 Worker 日志。

    Examples:
        hearth work logs --name gpu1           # 显示最后 50 行
        hearth work logs --name gpu1 -f        # 实时跟踪
        hearth work logs --name gpu1 --tail 100
    """
    stack_name = _get_worker_stack_name(name)

    state = read_stack_state(stack_name)
    if state is None:
        console.print(f"[red]未找到 Worker '{name}'[/red]")
        console.print(f"[dim]提示: 使用 'hearth work up -d --name {name}' 启动[/dim]")
        raise typer.Exit(1)

    if "worker" not in state.services:
        console.print(f"[red]状态文件中未找到 worker 服务[/red]")
        raise typer.Exit(1)

    svc = state.services["worker"]
    log_path = Path(svc.log_path)

    if not log_path.exists():
        console.print(f"[red]日志文件不存在: {log_path}[/red]")
        raise typer.Exit(1)

    if follow:
        # Use tail -f for real-time following
        console.print(f"[dim]跟踪日志: {log_path} (按 Ctrl+C 退出)[/dim]\n")
        proc = subprocess.Popen(
            ["tail", "-f", "-n", str(tail), str(log_path)],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            console.print("\n[dim]已停止跟踪[/dim]")
    else:
        # Read last N lines
        try:
            result = subprocess.run(
                ["tail", "-n", str(tail), str(log_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(f"[dim]日志: {log_path} (最后 {tail} 行)[/dim]\n")
                print(result.stdout, end="")
            else:
                console.print(f"[red]读取日志失败: {result.stderr}[/red]")
                raise typer.Exit(1)
        except FileNotFoundError:
            # tail command not available, fall back to Python
            console.print(f"[dim]日志: {log_path} (最后 {tail} 行)[/dim]\n")
            with open(log_path, "r") as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    print(line, end="")
