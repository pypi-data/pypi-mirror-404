import os
import subprocess
from pathlib import Path

import httpx


def check_ssh_key_available(ssh_host: str, ssh_user: str, ssh_port: int = 22) -> tuple[bool, str]:
    """
    Check if passwordless SSH key authentication is available to the target host.

    MCP cannot handle interactive password input, so SSH key is required for rsync mode.

    Returns:
        (success, message)
    """
    # Check if common SSH key files exist
    ssh_dir = Path.home() / ".ssh"
    key_files = ["id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"]
    has_key = any((ssh_dir / f).exists() for f in key_files)

    if not has_key:
        return (
            False,
            "No SSH key found in ~/.ssh/. MCP requires SSH key authentication for rsync mode.",
        )

    # Try passwordless SSH connection test
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",  # Disable password prompt
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=accept-new",
                "-p",
                str(ssh_port),
                f"{ssh_user}@{ssh_host}",
                "echo ok",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, "SSH key authentication successful"
        else:
            return False, (
                f"SSH key authentication failed. Please configure passwordless SSH to {ssh_user}@{ssh_host}. "
                f"Error: {result.stderr.strip()}"
            )
    except subprocess.TimeoutExpired:
        return False, f"SSH connection to {ssh_host} timed out"
    except FileNotFoundError:
        return False, "SSH client not found. Please install OpenSSH."
    except Exception as e:
        return False, f"SSH check failed: {e}"


class HearthMCPServer:
    def __init__(self, api_url: str | None = None, token: str | None = None):
        self.api_url = (
            api_url or os.environ.get("HEARTH_API_URL", "http://localhost:43110")
        ).rstrip("/")
        self.token = token or os.environ.get("HEARTH_API_TOKEN", "")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "hearth_hosts_list",
                "description": "列出所有可用的GPU主机及其状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "按状态过滤: online, offline, draining",
                            "enum": ["online", "offline", "draining"],
                        }
                    },
                },
            },
            {
                "name": "hearth_hosts_get",
                "description": "获取指定主机的详细信息，包括GPU型号、显存",
                "inputSchema": {
                    "type": "object",
                    "properties": {"host_id": {"type": "string", "description": "主机ID"}},
                    "required": ["host_id"],
                },
            },
            {
                "name": "hearth_run_create",
                "description": "创建并提交一个GPU计算任务",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {"type": "string", "description": "快照ID"},
                        "command": {"type": "string", "description": "执行命令"},
                        "host_id": {
                            "type": "string",
                            "description": "目标主机ID（从 hearth_hosts_list 获取）",
                        },
                        "gpu": {"type": "string", "description": "GPU要求", "default": "any"},
                        "name": {"type": "string", "description": "任务名称"},
                        "client_request_id": {
                            "type": "string",
                            "description": "幂等性key，用于防止重复创建（可选）",
                        },
                    },
                    "required": ["snapshot_id", "command", "host_id"],
                },
            },
            {
                "name": "hearth_runs_list",
                "description": "列出任务，支持按状态和主机过滤",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "按状态过滤: queued, dispatched, accepted, running, succeeded, failed, canceled, canceling",
                        },
                        "host_id": {
                            "type": "string",
                            "description": "按主机ID过滤",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量限制",
                            "default": 50,
                        },
                    },
                },
            },
            {
                "name": "hearth_run_status",
                "description": "获取任务的当前状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {"run_id": {"type": "string", "description": "任务ID"}},
                    "required": ["run_id"],
                },
            },
            {
                "name": "hearth_run_logs",
                "description": "获取任务的日志输出",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string", "description": "任务ID"},
                        "limit": {"type": "integer", "description": "返回行数", "default": 100},
                    },
                    "required": ["run_id"],
                },
            },
            {
                "name": "hearth_run_cancel",
                "description": "取消正在运行或排队中的任务",
                "inputSchema": {
                    "type": "object",
                    "properties": {"run_id": {"type": "string", "description": "任务ID"}},
                    "required": ["run_id"],
                },
            },
            {
                "name": "hearth_run_delete",
                "description": "删除已完成的任务记录（仅支持 succeeded/failed/canceled 状态）",
                "inputSchema": {
                    "type": "object",
                    "properties": {"run_id": {"type": "string", "description": "任务ID"}},
                    "required": ["run_id"],
                },
            },
            {
                "name": "hearth_run_retry",
                "description": "重试失败或已取消的任务（创建一个新任务使用相同参数）",
                "inputSchema": {
                    "type": "object",
                    "properties": {"run_id": {"type": "string", "description": "任务ID"}},
                    "required": ["run_id"],
                },
            },
            {
                "name": "hearth_snapshot_prepare",
                "description": "准备快照上传，获取预签名上传URL。客户端需要先上传到返回的URL，再调用confirm。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID，格式: sha256:<64位hex>",
                        },
                        "size_bytes": {
                            "type": "integer",
                            "description": "快照大小（字节）",
                        },
                        "name": {
                            "type": "string",
                            "description": "快照名称（可选）",
                        },
                    },
                    "required": ["snapshot_id", "size_bytes"],
                },
            },
            {
                "name": "hearth_snapshot_confirm",
                "description": "确认快照上传完成，在数据库中注册快照。需要先调用prepare并上传文件。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID",
                        },
                        "name": {
                            "type": "string",
                            "description": "快照名称（可选）",
                        },
                        "size_bytes": {
                            "type": "integer",
                            "description": "快照大小（字节）",
                        },
                        "manifest": {
                            "type": "object",
                            "description": "快照元数据（可选）",
                        },
                    },
                    "required": ["snapshot_id"],
                },
            },
            {
                "name": "hearth_snapshot_get",
                "description": "获取快照元数据",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID",
                        },
                    },
                    "required": ["snapshot_id"],
                },
            },
            {
                "name": "hearth_get_storage_mode",
                "description": "获取当前存储模式（s3或rsync）",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "hearth_snapshot_prepare_rsync",
                "description": "准备rsync上传快照。预留Worker并返回SSH连接信息。注意：MCP模式需要SSH key认证（无交互式密码）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID，格式: sha256:<64位hex>",
                        },
                        "size_bytes": {
                            "type": "integer",
                            "description": "tarball大小（字节）",
                        },
                        "host_id": {
                            "type": "string",
                            "description": "目标主机ID（推荐指定，确保快照上传到正确的Worker）",
                        },
                    },
                    "required": ["snapshot_id", "size_bytes"],
                },
            },
            {
                "name": "hearth_snapshot_upload_rsync",
                "description": "通过rsync上传快照tarball。需要SSH key认证。先调用hearth_snapshot_prepare_rsync获取SSH信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "local_tarball_path": {
                            "type": "string",
                            "description": "本地tarball文件路径",
                        },
                        "ticket": {
                            "type": "string",
                            "description": "从prepare_rsync获取的ticket",
                        },
                        "ssh_user": {
                            "type": "string",
                            "description": "SSH用户名",
                        },
                        "ssh_host": {
                            "type": "string",
                            "description": "SSH主机",
                        },
                        "ssh_port": {
                            "type": "integer",
                            "description": "SSH端口",
                        },
                        "inbox_path": {
                            "type": "string",
                            "description": "远程inbox目录路径",
                        },
                    },
                    "required": [
                        "local_tarball_path",
                        "ticket",
                        "ssh_user",
                        "ssh_host",
                        "ssh_port",
                        "inbox_path",
                    ],
                },
            },
            {
                "name": "hearth_snapshot_confirm_rsync",
                "description": "确认rsync上传完成。在成功rsync上传后调用，验证并注册快照",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID，格式: sha256:<64位hex>",
                        },
                        "ticket": {
                            "type": "string",
                            "description": "从prepare_rsync获取的ticket",
                        },
                    },
                    "required": ["snapshot_id", "ticket"],
                },
            },
            {
                "name": "hearth_snapshot_upload_relay",
                "description": "通过Controller中转上传快照（无需SSH key）。MCP上传文件到Controller，Controller再rsync到Worker。适用于MCP没有SSH key的场景。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "local_tarball_path": {
                            "type": "string",
                            "description": "本地tarball文件路径",
                        },
                        "snapshot_id": {
                            "type": "string",
                            "description": "快照ID，格式: sha256:<64位hex>",
                        },
                    },
                    "required": ["local_tarball_path", "snapshot_id"],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        handler = getattr(self, f"_handle_{name}", None)
        if not handler:
            return {"error": f"Unknown tool: {name}"}

        try:
            return await handler(arguments)
        except httpx.HTTPStatusError as e:
            # 改进错误信息，包含响应体
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            return {"error": f"API error: {e.response.status_code}", "detail": detail}
        except Exception as e:
            return {"error": str(e)}

    async def _handle_hearth_hosts_list(self, args: dict) -> dict:
        async with httpx.AsyncClient() as client:
            params = {}
            if args.get("status"):
                params["status_filter"] = args["status"]

            response = await client.get(
                f"{self.api_url}/api/v1/hosts",
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

            return {
                "hosts": [
                    {
                        "id": h["id"],
                        "name": h["name"],
                        "status": h["status"],
                        "gpu": h.get("gpu_name", "N/A"),
                        "gpu_vram_gb": h.get("gpu_vram_gb"),
                    }
                    for h in data.get("hosts", [])
                ]
            }

    async def _handle_hearth_hosts_get(self, args: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/hosts/{args['host_id']}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def _handle_hearth_run_create(self, args: dict) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "snapshot_id": args["snapshot_id"],
                "command": args["command"],
                "host_id": args["host_id"],  # Required field
                "resources": {"gpu": args.get("gpu", "any")},
                "name": args.get("name"),
            }
            # 添加 client_request_id 支持
            if args.get("client_request_id"):
                payload["client_request_id"] = args["client_request_id"]

            response = await client.post(
                f"{self.api_url}/api/v1/runs",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            result = response.json()

            return {
                "run_id": result["id"],
                "status": result["status"],
                "message": f"任务已创建: {result['id']}",
            }

    async def _handle_hearth_run_status(self, args: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/runs/{args['run_id']}",
                headers=self._headers(),
            )
            response.raise_for_status()
            run = response.json()

            return {
                "run_id": run["id"],
                "status": run["status"],
                "host_id": run.get("host_id"),
                "started_at": run.get("started_at"),
                "finished_at": run.get("finished_at"),
                "exit_code": run.get("exit_code"),
            }

    async def _handle_hearth_run_logs(self, args: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/runs/{args['run_id']}/logs",
                params={"limit": args.get("limit", 100)},
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

            return {
                "run_id": args["run_id"],
                "logs": data.get("content", ""),
                "has_more": data.get("has_more", False),
            }

    async def _handle_hearth_run_cancel(self, args: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/runs/{args['run_id']}/cancel",
                headers=self._headers(),
            )
            response.raise_for_status()
            return {"message": f"任务已取消: {args['run_id']}"}

    async def _handle_hearth_runs_list(self, args: dict) -> dict:
        """List runs with optional filtering."""
        async with httpx.AsyncClient() as client:
            params = {"limit": args.get("limit", 50)}
            if args.get("status"):
                params["status_filter"] = args["status"]
            if args.get("host_id"):
                params["host_id"] = args["host_id"]

            response = await client.get(
                f"{self.api_url}/api/v1/runs",
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

            return {
                "runs": [
                    {
                        "id": r["id"],
                        "name": r.get("name"),
                        "status": r["status"],
                        "host_id": r.get("host_id"),
                        "host_name": r.get("host_name"),
                        "command": r.get("command"),
                        "exit_code": r.get("exit_code"),
                        "created_at": r.get("created_at"),
                        "finished_at": r.get("finished_at"),
                    }
                    for r in data.get("runs", [])
                ],
                "total": data.get("total", 0),
            }

    async def _handle_hearth_run_delete(self, args: dict) -> dict:
        """Delete a completed run record."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_url}/api/v1/runs/{args['run_id']}",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                return {"error": f"API error: {response.status_code}", "detail": detail}
            return {"message": f"任务已删除: {args['run_id']}"}

    async def _handle_hearth_run_retry(self, args: dict) -> dict:
        """Retry a failed or canceled run."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/runs/{args['run_id']}/retry",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                return {"error": f"API error: {response.status_code}", "detail": detail}
            result = response.json()
            return {
                "new_run_id": result["id"],
                "status": result["status"],
                "message": f"已创建重试任务: {result['id']}",
            }

    async def _handle_hearth_snapshot_prepare(self, args: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/api/v1/snapshots/prepare",
                json={
                    "snapshot_id": args["snapshot_id"],
                    "size_bytes": args["size_bytes"],
                    "name": args.get("name"),
                },
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            return response.json()

    async def _handle_hearth_snapshot_confirm(self, args: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/api/v1/snapshots/confirm",
                json={
                    "snapshot_id": args["snapshot_id"],
                    "name": args.get("name"),
                    "size_bytes": args.get("size_bytes"),
                    "manifest": args.get("manifest"),
                },
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            return response.json()

    async def _handle_hearth_snapshot_get(self, args: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/api/v1/snapshots/{args['snapshot_id']}",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            return response.json()

    async def _handle_hearth_get_storage_mode(self, args: dict) -> dict:  # noqa: ARG002
        """Get the current storage mode of the controller."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.api_url}/api/v1/storage/mode",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            return response.json()

    async def _handle_hearth_snapshot_prepare_rsync(self, args: dict) -> dict:
        """
        Prepare for rsync upload of a snapshot.

        This will reserve a worker and return SSH connection info.
        Note: MCP requires SSH key authentication (no interactive password).
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "snapshot_id": args["snapshot_id"],
                "size_bytes": args["size_bytes"],
            }
            # Add host_id if provided
            if args.get("host_id"):
                payload["host_id"] = args["host_id"]

            response = await client.post(
                f"{self.api_url}/api/v1/snapshots/prepare-rsync",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}

            data = response.json()

            if data.get("already_exists"):
                return {"status": "already_exists", "snapshot_id": args["snapshot_id"]}

            # Check SSH key availability
            ssh_ok, ssh_msg = check_ssh_key_available(
                data["ssh_host"],
                data["ssh_user"],
                data.get("ssh_port", 22),
            )

            if not ssh_ok:
                return {
                    "status": "error",
                    "error": "ssh_key_required",
                    "message": ssh_msg,
                    "hint": "Use hearth_snapshot_upload_relay instead (no SSH key required).",
                }

            return {
                "status": "ready",
                "ticket": data["ticket"],
                "ssh_user": data["ssh_user"],
                "ssh_host": data["ssh_host"],
                "ssh_port": data.get("ssh_port", 22),
                "inbox_path": data["inbox_path"],
                "expires_at": data.get("expires_at"),
            }

    async def _handle_hearth_snapshot_upload_rsync(self, args: dict) -> dict:
        """
        Upload a snapshot tarball via rsync.

        This requires SSH key authentication (no password prompt).
        Use hearth_snapshot_prepare_rsync first to get the SSH info.
        """
        local_tarball_path = args["local_tarball_path"]
        ticket = args["ticket"]
        ssh_user = args["ssh_user"]
        ssh_host = args["ssh_host"]
        ssh_port = args["ssh_port"]
        inbox_path = args["inbox_path"]

        # Validate local file exists
        if not Path(local_tarball_path).exists():
            return {
                "status": "error",
                "error": "file_not_found",
                "message": f"Local tarball not found: {local_tarball_path}",
            }

        remote_path = f"{ssh_user}@{ssh_host}:{inbox_path}/{ticket}.tar.gz"
        rsync_cmd = [
            "rsync",
            "-avz",
            "--progress",
            "-e",
            f"ssh -p {ssh_port} -o BatchMode=yes -o StrictHostKeyChecking=accept-new",
            local_tarball_path,
            remote_path,
        ]

        try:
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
            )

            if result.returncode == 0:
                return {"status": "success", "ticket": ticket}
            else:
                return {
                    "status": "error",
                    "error": "rsync_failed",
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "timeout",
                "message": "rsync upload timed out after 5 minutes",
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": "rsync_not_found",
                "message": "rsync command not found. Please install rsync.",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _handle_hearth_snapshot_confirm_rsync(self, args: dict) -> dict:
        """
        Confirm rsync upload of a snapshot.

        Call this after successful rsync upload to verify and register the snapshot.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/api/v1/snapshots/confirm-rsync",
                json={
                    "snapshot_id": args["snapshot_id"],
                    "ticket": args["ticket"],
                },
                headers=self._headers(),
            )
            if response.status_code >= 400:
                return {"error": f"API error: {response.status_code}", "detail": response.json()}
            return response.json()

    async def _handle_hearth_snapshot_upload_relay(self, args: dict) -> dict:
        """
        Upload a snapshot via Controller relay (no SSH key required).

        Use this when SSH key authentication is not available.
        The file is uploaded to Controller via HTTPS, then relayed to Worker.

        Args:
            local_tarball_path: Path to the local tarball file
            snapshot_id: The snapshot ID (sha256:xxx format)

        Returns:
            Upload result
        """
        local_tarball_path = args["local_tarball_path"]
        snapshot_id = args["snapshot_id"]

        # Validate local file exists
        if not Path(local_tarball_path).exists():
            return {
                "status": "error",
                "error": "file_not_found",
                "message": f"Local tarball not found: {local_tarball_path}",
            }

        # Read file content
        try:
            with open(local_tarball_path, "rb") as f:
                content = f.read()
        except Exception as e:
            return {
                "status": "error",
                "error": "read_failed",
                "message": f"Failed to read file: {e}",
            }

        # Upload via multipart form
        async with httpx.AsyncClient(timeout=300.0) as client:
            files = {"file": ("snapshot.tar.gz", content, "application/gzip")}
            data = {"snapshot_id": snapshot_id}

            # Build headers without Content-Type (httpx will set it for multipart)
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = await client.post(
                f"{self.api_url}/api/v1/snapshots/upload-relay",
                files=files,
                data=data,
                headers=headers,
            )
            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                return {"error": f"API error: {response.status_code}", "detail": detail}
            return response.json()
