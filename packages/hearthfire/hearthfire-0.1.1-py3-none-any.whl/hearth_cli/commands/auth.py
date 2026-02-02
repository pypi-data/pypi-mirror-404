import os
import socket
import sys
from datetime import datetime

import httpx
import typer
from rich.console import Console

from hearth_cli.config import config

app = typer.Typer()
console = Console()


def _generate_default_pat_name() -> str:
    """Generate default PAT name: cli-<hostname>-<date>"""
    hostname = socket.gethostname()[:20]  # Truncate long hostnames
    date_str = datetime.now().strftime("%Y%m%d")
    return f"cli-{hostname}-{date_str}"


def _login_with_token(api_url: str, token: str) -> None:
    """Legacy login flow: directly use provided token"""
    try:
        response = httpx.get(
            f"{api_url.rstrip('/')}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
        user = response.json()

        config.api_url = api_url
        config.token = token

        display = user.get("display_name") or user.get("username")
        console.print(f"[green]登录成功！[/green]欢迎, {display}")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]登录失败:[/red] {e.response.status_code}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]连接失败:[/red] {e}")
        raise typer.Exit(1) from None


def _login_with_password(
    api_url: str,
    username: str,
    password: str,
    pat_name: str,
    expires_in_days: int | None,
    never_expires: bool,
    print_token: bool = False,
) -> None:
    """New login flow: username/password → access_token → create PAT → save → logout

    If print_token is True, suppress all console output and only print the token to stdout.
    """
    base_url = api_url.rstrip("/")

    # Step 1: Login with username/password
    if not print_token:
        console.print("[dim]正在登录...[/dim]")
    try:
        login_response = httpx.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10.0,
        )
        login_response.raise_for_status()
        login_data = login_response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            if not print_token:
                console.print("[red]登录失败:[/red] 用户名或密码错误")
            else:
                print("Error: Invalid username or password", file=sys.stderr)
        else:
            try:
                detail = e.response.json().get("detail", str(e.response.status_code))
            except Exception:
                detail = str(e.response.status_code)
            if not print_token:
                console.print(f"[red]登录失败:[/red] {detail}")
            else:
                print(f"Error: {detail}", file=sys.stderr)
        raise typer.Exit(1) from None
    except Exception as e:
        if not print_token:
            console.print(f"[red]连接失败:[/red] {e}")
        else:
            print(f"Error: Connection failed: {e}", file=sys.stderr)
        raise typer.Exit(1) from None

    access_token = login_data["access_token"]
    user = login_data.get("user", {})
    display = user.get("display_name") or user.get("username") or username

    # Step 2: Create PAT
    if not print_token:
        console.print("[dim]正在创建访问令牌...[/dim]")
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    pat_payload: dict = {"name": pat_name}
    if never_expires:
        pat_payload["never_expires"] = True
    elif expires_in_days:
        pat_payload["expires_in_days"] = expires_in_days
    else:
        pat_payload["expires_in_days"] = 90  # Default 90 days

    try:
        pat_response = httpx.post(
            f"{base_url}/api/v1/auth/tokens",
            json=pat_payload,
            headers=auth_headers,
            timeout=10.0,
        )
        pat_response.raise_for_status()
        pat_data = pat_response.json()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e.response.status_code))
        except Exception:
            detail = str(e.response.status_code)
        if not print_token:
            console.print(f"[red]创建访问令牌失败:[/red] {detail}")
        else:
            print(f"Error: Failed to create token: {detail}", file=sys.stderr)
        raise typer.Exit(1) from None
    except Exception as e:
        if not print_token:
            console.print(f"[red]创建访问令牌失败:[/red] {e}")
        else:
            print(f"Error: Failed to create token: {e}", file=sys.stderr)
        raise typer.Exit(1) from None

    pat_token = pat_data["token"]
    pat_token_name = pat_data.get("name", pat_name)
    expires_at = pat_data.get("expires_at")

    # Step 3: Save PAT to config
    config.api_url = api_url
    config.token = pat_token

    # Step 4: Logout session (revoke access_token)
    if not print_token:
        console.print("[dim]正在清理临时会话...[/dim]")
    try:
        httpx.post(
            f"{base_url}/api/v1/auth/logout",
            headers=auth_headers,
            timeout=10.0,
        )
    except Exception:
        # Logout failure is not critical, continue
        pass

    # Output based on mode
    if print_token:
        # --print-token mode: output ONLY the token to stdout
        print(pat_token)
    else:
        # Normal mode: rich console output
        console.print(f"[green]登录成功！[/green]欢迎, {display}")
        console.print(f"  [dim]访问令牌:[/dim] {pat_token_name}")
        if expires_at:
            console.print(f"  [dim]过期时间:[/dim] {expires_at}")
        elif never_expires:
            console.print("  [dim]过期时间:[/dim] 永不过期")


@app.command("login")
def login(
    api_url: str = typer.Option(None, "--url", "-u", help="API服务器地址"),
    token: str = typer.Option(None, "--token", "-t", help="API Token (直接使用已有Token)"),
    username: str = typer.Option(None, "--username", help="用户名"),
    password: str = typer.Option(None, "--password", "-p", help="密码 (非交互式)"),
    pat_name: str = typer.Option(None, "--pat-name", help="访问令牌名称"),
    expires_in_days: int = typer.Option(None, "--expires-in-days", help="令牌有效期（天）"),
    never_expires: bool = typer.Option(False, "--never-expires", help="令牌永不过期（仅管理员）"),
    print_token: bool = typer.Option(False, "--print-token", help="仅输出 token 到 stdout"),
) -> None:
    """登录到 Hearth 服务器

    默认模式: 使用用户名和密码登录，自动创建访问令牌。
    Token模式: 使用 --token 直接提供已有的 API Token。

    非交互式模式:
      - 使用 --password 或 HEARTH_PASSWORD 环境变量提供密码
      - 使用 --print-token 仅输出 token 到 stdout (用于脚本/CI)
    """
    if not api_url:
        api_url = typer.prompt("API服务器地址", default="http://localhost:43110")

    # Legacy mode: direct token input
    if token:
        _login_with_token(api_url, token)
        return

    # New mode: username/password login
    if not username:
        username = typer.prompt("用户名")

    # Password: --password > HEARTH_PASSWORD env > interactive prompt
    if not password:
        password = os.environ.get("HEARTH_PASSWORD")
    if not password:
        password = typer.prompt("密码", hide_input=True)

    if not pat_name:
        pat_name = _generate_default_pat_name()

    _login_with_password(
        api_url=api_url,
        username=username,
        password=password,
        pat_name=pat_name,
        expires_in_days=expires_in_days,
        never_expires=never_expires,
        print_token=print_token,
    )


@app.command("logout")
def logout() -> None:
    config.token = None
    console.print("[green]已登出[/green]")


@app.command("status")
def status() -> None:
    if not config.token:
        console.print("[yellow]未登录[/yellow]")
        return

    try:
        from hearth_cli.client import get_client

        client = get_client()
        user = client.get("/api/v1/auth/me")

        console.print("[green]已登录[/green]")
        console.print(f"  用户: {user['username']}")
        console.print(f"  角色: {user['role']}")
        console.print(f"  服务器: {config.api_url}")

    except Exception as e:
        console.print(f"[red]Token无效[/red]: {e}")
