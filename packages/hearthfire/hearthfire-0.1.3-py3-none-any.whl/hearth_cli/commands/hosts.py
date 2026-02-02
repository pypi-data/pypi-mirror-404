import os
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from hearth_cli.client import get_client

app = typer.Typer()
console = Console()


def get_known_hosts_path() -> Path:
    """Get Hearth's managed known_hosts file path."""
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        base = Path(state_home) / "hearth"
    else:
        base = Path.home() / ".local" / "state" / "hearth"

    return base / "known_hosts"


@app.command("list")
def list_hosts(
    status_filter: str = typer.Option(None, "--status", "-s", help="按状态过滤"),
    show_all: bool = typer.Option(False, "--all", "-a", help="显示所有主机(包括同hostname重复项)"),
    full_id: bool = typer.Option(False, "--full-id", "-f", help="显示完整ID而非短ID"),
) -> None:
    """
    列出GPU主机。

    默认按hostname去重，每个hostname只显示最佳主机（优先ACTIVE状态，最近心跳）。
    使用 --all 显示所有原始主机记录。
    """
    client = get_client()

    params = {}
    if status_filter:
        params["status_filter"] = status_filter
    if show_all:
        params["include_duplicates"] = "true"

    result = client.get("/api/v1/hosts", params=params)
    hosts = result.get("hosts", [])

    if not hosts:
        console.print("[dim]暂无主机[/dim]")
        return

    table = Table(title="GPU主机列表")
    table.add_column("ID (短)" if not full_id else "ID", style="cyan")
    table.add_column("名称")
    table.add_column("状态")
    table.add_column("GPU")
    table.add_column("显存")

    status_colors = {
        "online": "green",
        "offline": "red",
        "draining": "yellow",
    }

    for host in hosts:
        status_style = status_colors.get(host["status"], "white")

        gpu_name = host.get("gpu_name", "N/A")
        gpu_vram = f"{host['gpu_vram_gb']} GB" if host.get("gpu_vram_gb") else "N/A"

        display_id = host["id"] if full_id else host["id"][:12]

        table.add_row(
            display_id,
            host["name"],
            f"[{status_style}]{host['status']}[/{status_style}]",
            gpu_name,
            gpu_vram,
        )

    console.print(table)
    if not full_id:
        console.print("[dim]提示: 短ID可用于命令（如 --host），只要前缀唯一[/dim]")


@app.command("show")
def show_host(host_id: str) -> None:
    client = get_client()
    host = client.get(f"/api/v1/hosts/{host_id}")

    console.print(f"[bold]主机: {host['name']}[/bold]")
    console.print(f"  ID: {host['id']}")
    console.print(f"  状态: {host['status']}")
    console.print(f"  Tailscale IP: {host.get('tailscale_ip', 'N/A')}")
    console.print()

    # Display identity claims
    identities = host.get("identities", [])
    if identities:
        claims = identities[0].get("claims", {})
        console.print("[bold]身份信息:[/bold]")
        console.print(f"  hostname: {claims.get('hostname', 'N/A')}")
        console.print(f"  machine_id: {claims.get('machine_id', 'N/A')}")
        console.print(f"  dmi_uuid: {claims.get('dmi_uuid', 'N/A')}")
        console.print()

    # Display capabilities
    capabilities = host.get("capabilities", {})
    if capabilities:
        console.print("[bold]能力:[/bold]")
        for cap_name, cap_version in capabilities.items():
            console.print(f"  {cap_name}: {cap_version}")
        console.print()

    console.print("[bold]硬件信息:[/bold]")
    console.print(f"  CPU核心: {host.get('cpu_cores', 'N/A')}")
    console.print(f"  内存: {host.get('memory_gb', 'N/A')} GB")
    console.print(f"  磁盘: {host.get('disk_gb', 'N/A')} GB")
    console.print(f"  GPU: {host.get('gpu_name', 'N/A')}")
    console.print(f"  显存: {host.get('gpu_vram_gb', 'N/A')} GB")


@app.command("drain")
def drain_host(host_id: str) -> None:
    """将主机设置为draining状态，不再接受新任务。"""
    client = get_client()
    client.post(f"/api/v1/hosts/{host_id}/drain")
    console.print(f"主机 {host_id} 已设置为draining状态")


@app.command("approve")
def approve_host(host_id: str) -> None:
    """审批待注册的主机，使其可以接受任务。"""
    client = get_client()
    try:
        client.post(f"/api/v1/hosts/{host_id}/approve")
        console.print(f"[green]✓[/green] 主机 {host_id} 已审批通过")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            console.print(f"[red]✗[/red] 主机 {host_id} 不存在")
        elif "already approved" in error_msg.lower() or "400" in error_msg:
            console.print(f"[yellow]![/yellow] 主机 {host_id} 已经审批过或状态不允许审批")
        else:
            console.print(f"[red]✗[/red] 审批失败: {error_msg}")
        raise typer.Exit(1)


@app.command("trust")
def trust(
    host: str = typer.Argument(..., help="Host ID or prefix to trust"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
) -> None:
    """Trust a host's SSH key for rsync uploads.

    Fetches the host's SSH public key and adds it to Hearth's known_hosts.
    This must be done before rsync uploads will work.

    Example:
        hearth hosts trust K2__c
        hearth hosts trust K2__c --port 2222
    """
    from hearth_cli.client import APIError

    # Get effective SSH host from API
    client = get_client()
    try:
        metrics = client.get(f"/api/v1/hosts/{host}/metrics")
    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Host '{host}' not found[/red]")
        elif e.status_code == 400:
            # Ambiguous prefix
            console.print(f"[red]{e.message}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error fetching host metrics: {e}[/red]")
        raise typer.Exit(1)

    # Determine effective SSH host
    ssh_host = metrics.get("ssh_host") or metrics.get("observed_remote_addr")
    ssh_port = metrics.get("ssh_port") or port

    if not ssh_host:
        console.print("[red]Host has no SSH address configured[/red]")
        console.print("[dim]Worker must be connected or have HEARTH_SSH_HOST set[/dim]")
        raise typer.Exit(1)

    # Get known_hosts path
    known_hosts_path = get_known_hosts_path()
    known_hosts_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[blue]Fetching SSH key from {ssh_host}:{ssh_port}...[/blue]")

    # Run ssh-keyscan
    try:
        result = subprocess.run(
            ["ssh-keyscan", "-p", str(ssh_port), "-H", ssh_host],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Timeout fetching SSH key[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[red]ssh-keyscan not found. Install OpenSSH client.[/red]")
        raise typer.Exit(1)

    if result.returncode != 0 or not result.stdout.strip():
        console.print("[red]Failed to fetch SSH key[/red]")
        if result.stderr:
            console.print(f"[dim]stderr: {result.stderr}[/dim]")
        raise typer.Exit(1)

    # Append to known_hosts (avoid duplicates by checking existing content)
    existing = known_hosts_path.read_text() if known_hosts_path.exists() else ""
    new_keys = result.stdout.strip()

    if new_keys in existing:
        console.print("[yellow]Host key already trusted[/yellow]")
    else:
        with open(known_hosts_path, "a") as f:
            f.write(new_keys + "\n")
        console.print(f"[green]✓ Host key added to {known_hosts_path}[/green]")

    # Show fingerprint for user verification
    console.print("\n[dim]Key fingerprint(s):[/dim]")
    for line in new_keys.split("\n"):
        if line.strip():
            console.print(f"  {line[:60]}...")
