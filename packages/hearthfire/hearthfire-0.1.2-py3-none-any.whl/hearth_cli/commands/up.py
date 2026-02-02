"""Unified 'hearth up' command to start controller/webui/worker from one place."""

import os
import signal
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
import typer
from filelock import Timeout
from rich.console import Console

from hearth_cli.runtime_state import (
    ProcIdentity,
    ServiceState,
    StackState,
    acquire_lock,
    create_stack_state,
    get_log_dir,
    get_proc_identity,
    read_stack_state,
    remove_stack_state,
    verify_proc_identity,
    write_stack_state,
)

app = typer.Typer()
console = Console()


def _wait_for_ready(url: str, timeout: float = 10.0) -> bool:
    """Poll URL until it returns 200 or timeout.

    Args:
        url: The URL to poll (e.g., http://localhost:43110/health)
        timeout: Maximum time to wait in seconds

    Returns:
        True if the URL returned 200 within timeout, False otherwise
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = httpx.get(url, timeout=1.0)
            if resp.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return False


class ServiceType(str, Enum):
    """Service types that can be started."""

    controller = "controller"
    webui = "webui"  # Kept for --dev-webui mode
    worker = "worker"


# Global list to track child processes for cleanup
_child_processes: list[subprocess.Popen] = []
_shutdown_requested = False
# Lock held during foreground mode to prevent concurrent starts
_stack_lock = None


def _signal_handler(signum: int, frame) -> None:
    """Handle Ctrl+C and other signals - terminate all children."""
    global _shutdown_requested
    if _shutdown_requested:
        return  # Already handling shutdown
    _shutdown_requested = True

    console.print("\n[yellow]收到中断信号，正在终止所有服务...[/yellow]")
    _terminate_all_children()


def _terminate_all_children() -> None:
    """Terminate all child processes gracefully, then force if needed."""
    for proc in _child_processes:
        if proc.poll() is None:  # Still running
            try:
                proc.terminate()
            except OSError:
                pass

    # Wait briefly for graceful shutdown
    for proc in _child_processes:
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # Force kill if still running
            try:
                proc.kill()
                proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                pass


def _start_controller(host: str, port: int) -> subprocess.Popen:
    """Start the controller service from the same Python environment as CLI."""
    cmd = [
        sys.executable,
        "-m",
        "hearth_controller.main",
        "--host",
        host,
        "--port",
        str(port),
    ]
    console.print(f"[blue]启动 Controller: {host}:{port}[/blue]")
    console.print(f"[dim]命令: {' '.join(cmd)}[/dim]")

    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    _child_processes.append(proc)
    return proc


def _start_webui(host: str, port: int, webui_dir: Path) -> subprocess.Popen:
    """Start the WebUI dev server."""
    # Set environment for Vite
    env = os.environ.copy()
    env["HOST"] = host

    cmd = ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    console.print(f"[blue]启动 WebUI: {host}:{port}[/blue]")
    console.print(f"[dim]命令: {' '.join(cmd)} (cwd={webui_dir})[/dim]")

    proc = subprocess.Popen(
        cmd,
        cwd=webui_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env,
    )
    _child_processes.append(proc)
    return proc


def _start_worker(
    controller_url: str,
    ssh_host: str,
    ssh_user: str,
    ssh_port: int,
) -> subprocess.Popen:
    """Start the worker agent using installed entrypoint."""
    env = os.environ.copy()
    env["HEARTH_CONTROLLER_URL"] = controller_url
    env["HEARTH_SSH_HOST"] = ssh_host
    env["HEARTH_SSH_USER"] = ssh_user
    env["HEARTH_SSH_PORT"] = str(ssh_port)

    cmd = [sys.executable, "-m", "hearth_worker"]
    console.print(f"[blue]启动 Worker: {ssh_user}@{ssh_host}:{ssh_port}[/blue]")
    console.print(f"[dim]命令: {' '.join(cmd)}[/dim]")
    console.print(f"[dim]HEARTH_CONTROLLER_URL={controller_url}[/dim]")

    proc = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env,
    )
    _child_processes.append(proc)
    return proc


def _find_project_root() -> Path:
    """Find the project root (where webui/ is located)."""
    # Start from CLI package and go up
    current = Path(__file__).resolve()
    for _ in range(10):  # Max 10 levels up
        current = current.parent
        if (current / "webui").is_dir():
            return current
    # Fallback to cwd
    cwd = Path.cwd()
    if (cwd / "webui").is_dir():
        return cwd
    raise RuntimeError("无法找到项目根目录 (webui/ 不存在)")


def _parse_ssh_target(ssh_target: str) -> tuple[str, str]:
    """Parse user@host format into (user, host)."""
    if "@" not in ssh_target:
        raise typer.BadParameter(f"SSH target must be in format user@host, got: {ssh_target}")
    user, host = ssh_target.split("@", 1)
    if not user or not host:
        raise typer.BadParameter(f"Invalid SSH target format: {ssh_target}")
    return user, host


def _monitor_processes(processes: list[subprocess.Popen]) -> int:
    """Monitor processes and return exit code when any exits."""
    global _shutdown_requested

    while not _shutdown_requested:
        for proc in processes:
            ret = proc.poll()
            if ret is not None:
                # A process exited
                return ret

        # Brief sleep to avoid busy-waiting
        try:
            import time

            time.sleep(0.5)
        except KeyboardInterrupt:
            # Handled by signal handler
            break

    return 0


def _start_service_detached(
    name: str,
    cmd: list[str],
    log_dir: Path,
    env: Optional[dict[str, str]] = None,
    cwd: Optional[Path] = None,
    ports: Optional[dict[str, int]] = None,
) -> tuple[subprocess.Popen, ServiceState]:
    """Start a service in detached mode with logging.

    Returns the Popen object and ServiceState for state file.
    """
    log_path = log_dir / f"{name}.log"

    # Prepare environment
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    # Open log file for output
    log_file = open(log_path, "w")

    # Start process in new session (detached from terminal)
    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=proc_env,
        cwd=cwd,
        start_new_session=True,  # Creates new process group
    )

    # Get process group ID
    pgid = os.getpgid(proc.pid)

    # Get process identity for later verification
    proc_identity = get_proc_identity(proc.pid)
    if proc_identity is None:
        # Process may have exited immediately
        proc_identity = ProcIdentity(start_time="0", cmdline=cmd)

    service_state = ServiceState(
        pid=proc.pid,
        pgid=pgid,
        argv=cmd,
        ports=ports or {},
        log_path=str(log_path),
        proc_identity=proc_identity,
    )

    return proc, service_state


def _start_controller_detached(
    host: str, port: int, log_dir: Path
) -> tuple[subprocess.Popen, ServiceState]:
    """Start controller in detached mode from the same Python environment as CLI."""
    cmd = [
        sys.executable,
        "-m",
        "hearth_controller.main",
        "--host",
        host,
        "--port",
        str(port),
    ]
    return _start_service_detached("controller", cmd, log_dir, ports={"http": port})


def _start_webui_detached(
    host: str, port: int, webui_dir: Path, log_dir: Path
) -> tuple[subprocess.Popen, ServiceState]:
    """Start WebUI in detached mode."""
    cmd = ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    env = {"HOST": host}
    return _start_service_detached(
        "webui", cmd, log_dir, env=env, cwd=webui_dir, ports={"http": port}
    )


def _start_worker_detached(
    controller_url: str,
    ssh_host: str,
    ssh_user: str,
    ssh_port: int,
    log_dir: Path,
) -> tuple[subprocess.Popen, ServiceState]:
    """Start worker in detached mode from the same Python environment as CLI."""
    cmd = [sys.executable, "-m", "hearth_worker"]
    env = {
        "HEARTH_CONTROLLER_URL": controller_url,
        "HEARTH_SSH_HOST": ssh_host,
        "HEARTH_SSH_USER": ssh_user,
        "HEARTH_SSH_PORT": str(ssh_port),
    }
    return _start_service_detached("worker", cmd, log_dir, env=env, ports={"ssh": ssh_port})


def _cleanup_services(services: dict[str, ServiceState]) -> None:
    """Cleanup already-started services on partial failure."""
    for name, svc in services.items():
        try:
            # Kill the process group
            os.killpg(svc.pgid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass

    # Brief wait for graceful shutdown
    import time

    time.sleep(1)

    # Force kill if still running
    for name, svc in services.items():
        try:
            os.killpg(svc.pgid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass


def _run_detached(
    stack_name: str,
    log_dir: Path,
    only: Optional[ServiceType],
    with_worker: bool,
    dev_webui: bool,
    controller_host: str,
    controller_port: int,
    webui_host: str,
    webui_port: int,
    webui_dir: Optional[Path],
    ssh_target: Optional[str],
    ssh_port: int,
    controller_url: Optional[str],
) -> None:
    """Run services in detached mode and return immediately."""
    # Try to acquire lock (non-blocking)
    try:
        lock = acquire_lock(stack_name, timeout=0)
    except Timeout:
        # Check if existing stack is still running
        existing_state = read_stack_state(stack_name)
        if existing_state:
            # Verify at least one service is still running
            any_running = False
            for svc_name, svc in existing_state.services.items():
                if verify_proc_identity(svc.pid, svc.proc_identity):
                    any_running = True
                    break

            if any_running:
                console.print(f"[red]错误: 名为 '{stack_name}' 的服务已在运行[/red]")
                console.print(f"[dim]状态文件: {read_stack_state(stack_name)}[/dim]")
                raise typer.Exit(1)
            else:
                # Stale state, clean it up
                remove_stack_state(stack_name)
                # Try lock again
                try:
                    lock = acquire_lock(stack_name, timeout=0)
                except Timeout:
                    console.print(f"[red]错误: 无法获取锁 '{stack_name}'[/red]")
                    raise typer.Exit(1)
        else:
            console.print(f"[red]错误: 无法获取锁 '{stack_name}'[/red]")
            raise typer.Exit(1)

    # Prepare log directory
    stack_log_dir = log_dir
    stack_log_dir.mkdir(parents=True, exist_ok=True)

    services: dict[str, ServiceState] = {}
    started_procs: list[subprocess.Popen] = []

    try:
        if only:
            # --only mode
            if only == ServiceType.controller:
                proc, state = _start_controller_detached(
                    controller_host, controller_port, stack_log_dir
                )
                started_procs.append(proc)
                services["controller"] = state
                console.print(f"[blue]启动 Controller: {controller_host}:{controller_port}[/blue]")

                # Poll for readiness
                health_url = f"http://{controller_host if controller_host != '0.0.0.0' else 'localhost'}:{controller_port}/health"
                console.print(f"[dim]等待 Controller 就绪 (polling {health_url})...[/dim]")
                if not _wait_for_ready(health_url):
                    raise RuntimeError(
                        f"Controller 未能在 10 秒内就绪，日志: {stack_log_dir / 'controller.log'}"
                    )

            elif only == ServiceType.webui:
                assert webui_dir is not None  # Validated earlier
                proc, state = _start_webui_detached(
                    webui_host, webui_port, webui_dir, stack_log_dir
                )
                started_procs.append(proc)
                services["webui"] = state
                console.print(f"[blue]启动 WebUI: {webui_host}:{webui_port}[/blue]")

            elif only == ServiceType.worker:
                assert ssh_target is not None  # Validated earlier
                ssh_user, ssh_host = _parse_ssh_target(ssh_target)
                worker_controller_url = controller_url or f"ws://localhost:{controller_port}"
                proc, state = _start_worker_detached(
                    worker_controller_url, ssh_host, ssh_user, ssh_port, stack_log_dir
                )
                started_procs.append(proc)
                services["worker"] = state
                console.print(f"[blue]启动 Worker: {ssh_user}@{ssh_host}:{ssh_port}[/blue]")
        else:
            # Default mode: controller only (WebUI served by controller)
            # Optionally: + dev webui + worker
            # Start controller
            proc, state = _start_controller_detached(
                controller_host, controller_port, stack_log_dir
            )
            started_procs.append(proc)
            services["controller"] = state
            console.print(f"[blue]启动 Controller: {controller_host}:{controller_port}[/blue]")

            # Poll for controller readiness (HTTP health check)
            health_url = f"http://{controller_host if controller_host != '0.0.0.0' else 'localhost'}:{controller_port}/health"
            console.print(f"[dim]等待 Controller 就绪 (polling {health_url})...[/dim]")
            if not _wait_for_ready(health_url):
                raise RuntimeError(
                    f"Controller 未能在 10 秒内就绪，日志: {stack_log_dir / 'controller.log'}"
                )
            console.print("[green]Controller 已就绪[/green]")

            # Start webui dev server if --dev-webui
            if dev_webui:
                assert webui_dir is not None  # Validated earlier
                proc, state = _start_webui_detached(
                    webui_host, webui_port, webui_dir, stack_log_dir
                )
                started_procs.append(proc)
                services["webui"] = state
                console.print(f"[blue]启动 WebUI (dev): {webui_host}:{webui_port}[/blue]")

                time.sleep(0.5)
                if proc.poll() is not None:
                    raise RuntimeError(f"WebUI 启动失败，退出码: {proc.returncode}")

            # Start worker if requested
            if with_worker:
                assert ssh_target is not None  # Validated earlier
                ssh_user, ssh_host = _parse_ssh_target(ssh_target)
                worker_controller_url = controller_url or f"ws://localhost:{controller_port}"
                proc, state = _start_worker_detached(
                    worker_controller_url, ssh_host, ssh_user, ssh_port, stack_log_dir
                )
                started_procs.append(proc)
                services["worker"] = state
                console.print(f"[blue]启动 Worker: {ssh_user}@{ssh_host}:{ssh_port}[/blue]")

                time.sleep(0.2)
                if proc.poll() is not None:
                    raise RuntimeError(f"Worker 启动失败，退出码: {proc.returncode}")

        # Write state file
        stack_state = create_stack_state(stack_name, services)
        write_stack_state(stack_state)

        console.print(f"\n[green]✓ 服务已在后台启动 (name={stack_name})[/green]")
        console.print(f"[dim]日志目录: {stack_log_dir}[/dim]")
        console.print(f"[dim]使用 'hearth down --name {stack_name}' 停止服务[/dim]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        # Cleanup already-started services
        if services:
            console.print("[yellow]正在清理已启动的服务...[/yellow]")
            _cleanup_services(services)
            remove_stack_state(stack_name)
        lock.release()
        raise typer.Exit(1)

    finally:
        # Always release lock - detached processes run independently
        lock.release()


@app.callback(invoke_without_command=True)
def up(
    ctx: typer.Context,
    only: Optional[ServiceType] = typer.Option(
        None,
        "--only",
        help="仅启动指定服务 (controller, webui, worker)",
    ),
    with_worker: bool = typer.Option(
        False,
        "--with-worker",
        help="同时启动 Worker (需要 --ssh-target)",
    ),
    dev_webui: bool = typer.Option(
        False,
        "--dev-webui",
        help="启动 Vite 开发服务器 (需要 webui/ 目录)",
    ),
    controller_host: str = typer.Option(
        "0.0.0.0",
        "--controller-host",
        help="Controller 绑定地址",
    ),
    controller_port: int = typer.Option(
        43110,
        "--controller-port",
        help="Controller 端口",
    ),
    webui_host: str = typer.Option(
        "0.0.0.0",
        "--webui-host",
        help="WebUI 绑定地址 (仅 --dev-webui 模式)",
    ),
    webui_port: int = typer.Option(
        5173,
        "--webui-port",
        help="WebUI 端口 (仅 --dev-webui 模式)",
    ),
    ssh_target: Optional[str] = typer.Option(
        None,
        "--ssh-target",
        help="Worker SSH 目标 (格式: user@host)",
    ),
    ssh_port: int = typer.Option(
        22,
        "--ssh-port",
        help="Worker SSH 端口",
    ),
    controller_url: Optional[str] = typer.Option(
        None,
        "--controller-url",
        help="Worker 连接的 Controller URL (默认: ws://localhost:43110)",
    ),
    detach: bool = typer.Option(
        False,
        "--detach",
        "-d",
        help="后台模式运行，立即返回",
    ),
    name: str = typer.Option(
        "default",
        "--name",
        help="服务栈名称 (用于后台模式)",
    ),
    log_dir: Optional[Path] = typer.Option(
        None,
        "--log-dir",
        help="日志目录 (默认: ~/.local/state/hearth/logs/<name>)",
    ),
) -> None:
    """启动 Hearth 服务。

    默认启动 Controller (WebUI 由 Controller 静态文件服务提供)。

    Examples:
        hearth up                           # 启动 controller (含 WebUI)
        hearth up --dev-webui               # 启动 controller + Vite 开发服务器
        hearth up --only controller         # 仅启动 controller
        hearth up --only webui              # 仅启动 webui (需要 webui/ 目录)
        hearth up --only worker --ssh-target user@host  # 启动 worker
        hearth up --with-worker --ssh-target user@host  # controller + worker
        hearth up -d --name dev             # 后台启动，名为 dev
    """
    # Validate worker requirements
    if only == ServiceType.worker and not ssh_target:
        console.print("[red]错误: --only worker 需要 --ssh-target 参数[/red]")
        raise typer.Exit(1)

    if with_worker and not ssh_target:
        console.print("[red]错误: --with-worker 需要 --ssh-target 参数[/red]")
        raise typer.Exit(1)

    # Only find project root when --dev-webui or --only webui is used
    webui_dir: Optional[Path] = None
    if dev_webui or only == ServiceType.webui:
        try:
            project_root = _find_project_root()
            webui_dir = project_root / "webui"
        except RuntimeError as e:
            console.print(f"[red]错误: {e}[/red]")
            raise typer.Exit(1)

    # Detach mode: start in background and return
    if detach:
        stack_log_dir = get_log_dir(name, log_dir)
        _run_detached(
            stack_name=name,
            log_dir=stack_log_dir,
            only=only,
            with_worker=with_worker,
            dev_webui=dev_webui,
            controller_host=controller_host,
            controller_port=controller_port,
            webui_host=webui_host,
            webui_port=webui_port,
            webui_dir=webui_dir,
            ssh_target=ssh_target,
            ssh_port=ssh_port,
            controller_url=controller_url,
        )
        return

    # Foreground mode: original behavior
    # Setup signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    processes: list[subprocess.Popen] = []

    try:
        # Start services based on options
        if only:
            # --only mode: start only the specified service
            if only == ServiceType.controller:
                proc = _start_controller(controller_host, controller_port)
                processes.append(proc)

            elif only == ServiceType.webui:
                assert webui_dir is not None  # Validated earlier
                proc = _start_webui(webui_host, webui_port, webui_dir)
                processes.append(proc)

            elif only == ServiceType.worker:
                assert ssh_target is not None  # Validated earlier
                ssh_user, ssh_host = _parse_ssh_target(ssh_target)
                worker_controller_url = controller_url or f"ws://localhost:{controller_port}"
                proc = _start_worker(worker_controller_url, ssh_host, ssh_user, ssh_port)
                processes.append(proc)

        else:
            # Default mode: controller only (WebUI served by controller)
            # Optionally: + dev webui + worker
            proc_controller = _start_controller(controller_host, controller_port)
            processes.append(proc_controller)

            # Start webui dev server if --dev-webui
            if dev_webui:
                assert webui_dir is not None  # Validated earlier
                proc_webui = _start_webui(webui_host, webui_port, webui_dir)
                processes.append(proc_webui)

            if with_worker:
                assert ssh_target is not None  # Validated earlier
                ssh_user, ssh_host = _parse_ssh_target(ssh_target)
                worker_controller_url = controller_url or f"ws://localhost:{controller_port}"
                proc_worker = _start_worker(worker_controller_url, ssh_host, ssh_user, ssh_port)
                processes.append(proc_worker)

        console.print("\n[green]✓ 服务已启动，按 Ctrl+C 终止[/green]\n")

        # Monitor processes
        exit_code = _monitor_processes(processes)

        if exit_code != 0 and not _shutdown_requested:
            console.print(f"\n[red]错误: 服务异常退出 (code={exit_code})[/red]")
            _terminate_all_children()
            raise typer.Exit(exit_code)

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        _terminate_all_children()
        raise typer.Exit(1)

    finally:
        _terminate_all_children()

    console.print("[green]✓ 所有服务已停止[/green]")
