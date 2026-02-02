import sys

import httpx
import typer

from hearth_cli.client import APIError
from hearth_cli.commands import (
    admin,
    auth,
    cache,
    down,
    hosts,
    runs,
    snapshots,
    status,
    up,
    users,
    work,
)

app = typer.Typer(
    name="hearth",
    help="Hearth - 分布式GPU任务调度系统",
    no_args_is_help=True,
)

app.add_typer(admin.app, name="admin", help="管理员命令")
app.add_typer(auth.app, name="auth", help="认证管理")
app.add_typer(cache.app, name="cache", help="缓存管理")
app.add_typer(down.app, name="down", help="停止服务")
app.add_typer(hosts.app, name="hosts", help="主机管理")
app.add_typer(runs.app, name="runs", help="任务管理")
app.add_typer(snapshots.app, name="snapshots", help="快照管理")
app.add_typer(status.app, name="status", help="服务状态")
app.add_typer(users.app, name="users", help="用户管理")
app.add_typer(up.app, name="up", help="启动服务")
app.add_typer(work.app, name="work", help="Worker 生命周期管理")


@app.callback()
def main() -> None:
    pass


def cli() -> None:
    try:
        app()
    except APIError as e:
        if e.status_code == 401:
            typer.secho("错误: 认证失败，请运行 'hearth auth login' 重新登录", fg=typer.colors.RED)
        elif e.status_code == 404:
            typer.secho(f"错误: 资源未找到 - {e.message}", fg=typer.colors.RED)
        elif e.status_code >= 500:
            typer.secho(f"错误: 服务器错误 ({e.status_code}): {e.message}", fg=typer.colors.RED)
        else:
            typer.secho(f"错误: API返回 {e.status_code} - {e.message}", fg=typer.colors.RED)
        sys.exit(1)
    except httpx.ConnectError:
        typer.secho("错误: 无法连接到服务器，请检查网络和API地址", fg=typer.colors.RED)
        sys.exit(1)
    except httpx.TimeoutException:
        typer.secho("错误: 请求超时，服务器响应过慢", fg=typer.colors.RED)
        sys.exit(1)
    except RuntimeError as e:
        typer.secho(f"错误: {e}", fg=typer.colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    cli()
