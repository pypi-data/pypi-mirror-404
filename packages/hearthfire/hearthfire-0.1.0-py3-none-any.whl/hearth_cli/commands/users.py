import typer
from rich.console import Console
from rich.table import Table

from hearth_cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("list")
def list_users() -> None:
    """列出所有用户 (仅管理员)"""
    client = get_client()
    result = client.get("/api/v1/users")

    users = result.get("users", [])
    if not users:
        console.print("[yellow]暂无用户[/yellow]")
        return

    table = Table(title="用户列表")
    table.add_column("ID", style="dim")
    table.add_column("用户名", style="cyan")
    table.add_column("显示名")
    table.add_column("角色", style="magenta")
    table.add_column("状态")

    for user in users:
        status = "[green]活跃[/green]" if user.get("is_active", True) else "[red]禁用[/red]"
        table.add_row(
            user["id"],
            user["username"],
            user.get("display_name") or "-",
            user.get("role", "user"),
            status,
        )

    console.print(table)
    console.print(f"\n共 {result.get('total', len(users))} 个用户")


@app.command("create")
def create_user(
    username: str = typer.Option(..., "--username", "-u", help="用户名"),
    display_name: str = typer.Option(None, "--display-name", "-d", help="显示名称"),
    password: str = typer.Option(None, "--password", "-p", help="密码 (不指定则自动生成)"),
    role: str = typer.Option("user", "--role", "-r", help="角色 (user/admin)"),
) -> None:
    """创建新用户 (仅管理员)"""
    client = get_client()

    data: dict = {"username": username, "role": role}
    if display_name:
        data["display_name"] = display_name
    if password:
        data["password"] = password

    result = client.post("/api/v1/users", data)
    user_id = result["id"]

    console.print(f"[green]用户创建成功![/green]")
    console.print(f"  用户ID: {user_id}")
    console.print(f"  用户名: {result['username']}")

    # 如果未指定密码，调用 reset-password 获取生成的密码
    if not password:
        reset_result = client.post(f"/api/v1/users/{user_id}/reset-password", {})
        new_password = reset_result.get("new_password")
        if new_password:
            console.print()
            console.print(
                "[yellow]═══════════════════════════════════════════════════════════[/yellow]"
            )
            console.print(f"[bold yellow]初始密码: {new_password}[/bold yellow]")
            console.print(
                "[yellow]═══════════════════════════════════════════════════════════[/yellow]"
            )
            console.print("[red bold]⚠ 只显示一次，请妥善保存！[/red bold]")


@app.command("reset-password")
def reset_password(
    user_id: str = typer.Argument(..., help="用户ID"),
    password: str = typer.Option(None, "--password", "-p", help="新密码 (不指定则自动生成)"),
) -> None:
    """重置用户密码 (仅管理员)"""
    client = get_client()

    data: dict = {}
    if password:
        data["password"] = password

    result = client.post(f"/api/v1/users/{user_id}/reset-password", data)

    console.print(f"[green]密码重置成功![/green]")

    new_password = result.get("new_password")
    if new_password:
        console.print()
        console.print(
            "[yellow]═══════════════════════════════════════════════════════════[/yellow]"
        )
        console.print(f"[bold yellow]新密码: {new_password}[/bold yellow]")
        console.print(
            "[yellow]═══════════════════════════════════════════════════════════[/yellow]"
        )
        console.print("[red bold]⚠ 只显示一次，请妥善保存！[/red bold]")
    else:
        console.print(result.get("message", "密码已更新"))
