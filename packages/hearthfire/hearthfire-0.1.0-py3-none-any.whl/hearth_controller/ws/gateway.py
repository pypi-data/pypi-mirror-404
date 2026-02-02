"""
WebSocket Gateway for Worker Connections

Implements challenge-response authentication using Ed25519 signatures.
"""

import asyncio
import contextlib
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, update, case

from hearth_common.protocol.version import PROTOCOL_VERSION
from hearth_common.protocol.ws_messages import MessageType, TaskCanceledPayload
from hearth_controller.db.models import Host, HostMetricsLatest, Run, RunLog
from hearth_controller.db.session import async_session_maker
from hearth_controller.services.identity import (
    HostStatus,
    IdentityError,
    IdentityService,
    InvalidSignatureError,
    IdentityRevokedError,
)
from hearth_controller.ws.client_gateway import get_client_gateway

logger = logging.getLogger(__name__)

HANDSHAKE_TIMEOUT = 10.0
HEARTBEAT_INTERVAL = 30
MAX_PAYLOAD_SIZE = 64 * 1024  # 64KB max for claims/hardware


class WorkerConnection:
    """Represents an authenticated worker connection."""

    def __init__(
        self,
        websocket: WebSocket,
        host_id: str,
        host_status: str,
        remote_addr: str | None = None,
        remote_port: int | None = None,
    ) -> None:
        self.websocket = websocket
        self.host_id = host_id
        self.host_status = host_status
        self.remote_addr = remote_addr
        self.remote_port = remote_port
        self.seq = 0
        self.last_seen_seq = 0
        self.connected_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq

    async def send(self, msg_type: str, payload: dict, run_id: str | None = None) -> None:
        message = {
            "type": msg_type,
            "payload": payload,
            "message_id": uuid4().hex,
            "worker_id": self.host_id,
            "run_id": run_id,
            "seq": self.next_seq(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.websocket.send_json(message)

    async def send_error(self, code: str, message: str, retryable: bool = False) -> None:
        await self.send(
            MessageType.ERROR.value,
            {"code": code, "message": message, "retryable": retryable},
        )


class WorkerGateway:
    """Manages authenticated WebSocket connections from workers."""

    def __init__(self, auto_approve: bool = False) -> None:
        self.connections: dict[str, WorkerConnection] = {}
        self._lock = asyncio.Lock()
        self.auto_approve = auto_approve

    async def register_connection(
        self, websocket: WebSocket, host_id: str, host_status: str
    ) -> WorkerConnection:
        """Register an authenticated worker connection."""
        # Extract remote address from websocket
        remote_addr: str | None = None
        remote_port: int | None = None
        client = websocket.client
        if client:
            remote_addr, remote_port = client

        async with self._lock:
            if host_id in self.connections:
                old_conn = self.connections[host_id]
                with contextlib.suppress(Exception):
                    await old_conn.websocket.close()

            conn = WorkerConnection(websocket, host_id, host_status, remote_addr, remote_port)
            self.connections[host_id] = conn

            host_name = None
            async with async_session_maker() as db:
                host = await db.get(Host, host_id)
                if host:
                    host_name = host.name
                    if host.status != HostStatus.PENDING.value:
                        host.status = HostStatus.ACTIVE.value
                        host.last_heartbeat_at = datetime.now(timezone.utc)
                        await db.commit()

            logger.info(f"Worker {host_id} connected (status: {host_status})")

            # Broadcast host status to frontend clients (use actual status, not always "active")
            client_gw = get_client_gateway()
            await client_gw.broadcast_host_status(host_id, host_status, host_name)

            return conn

    async def disconnect(self, host_id: str) -> None:
        """Handle worker disconnection."""
        host_name = None
        async with self._lock:
            if host_id in self.connections:
                del self.connections[host_id]

            async with async_session_maker() as db:
                host = await db.get(Host, host_id)
                if host:
                    host_name = host.name
                    if host.status == HostStatus.ACTIVE.value:
                        host.status = HostStatus.OFFLINE.value
                        await db.commit()

            logger.info(f"Worker {host_id} disconnected")

        # Broadcast host offline to frontend clients
        client_gw = get_client_gateway()
        await client_gw.broadcast_host_status(host_id, "offline", host_name)

    def get_connection(self, host_id: str) -> WorkerConnection | None:
        return self.connections.get(host_id)

    async def dispatch_task(self, run: Run, host: Host) -> bool:
        conn = self.get_connection(host.id)
        if not conn:
            return False

        try:
            attempt_id = f"att_{uuid4().hex[:16]}"
            # Store attempt_id in DB for correlation
            from hearth_controller.db.session import async_session_maker

            async with async_session_maker() as session:
                from sqlalchemy import update

                await session.execute(
                    update(Run).where(Run.id == run.id).values(current_attempt_id=attempt_id)
                )
                await session.commit()

            await conn.send(
                MessageType.DISPATCH_TASK.value,
                {
                    "run_id": run.id,
                    "attempt_id": attempt_id,
                    "snapshot_id": run.snapshot_id,
                    "command": run.command,
                    "working_dir": run.working_dir,
                    "env": json.loads(run.env) if run.env else {},
                    "timeout_seconds": 3600,
                },
                run_id=run.id,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch task to {host.id}: {e}")
            return False

    async def cancel_task(self, host_id: str, run_id: str, attempt_id: str | None = None) -> bool:
        conn = self.get_connection(host_id)
        if not conn:
            return False

        try:
            payload = {"run_id": run_id}
            if attempt_id is not None:
                payload["attempt_id"] = attempt_id
            await conn.send(MessageType.CANCEL_TASK.value, payload, run_id=run_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task on {host_id}: {e}")
            return False

    async def dispatch_task_by_id(self, run_id: str, host_id: str) -> bool:
        """
        Dispatch a task by ID (for use after transaction commit).

        Fetches run data from DB and dispatches to the specified host.
        Returns False if host is disconnected or run not found.
        """
        conn = self.get_connection(host_id)
        if not conn:
            return False

        # Fetch run data from DB
        from hearth_controller.db.session import async_session_maker
        from sqlalchemy import update

        async with async_session_maker() as session:
            from hearth_controller.db.models import Run

            run = await session.get(Run, run_id)
            if not run:
                logger.error(f"Run {run_id} not found for dispatch")
                return False

            # Generate and persist attempt_id before dispatch
            attempt_id = f"att_{uuid4().hex[:16]}"
            await session.execute(
                update(Run).where(Run.id == run_id).values(current_attempt_id=attempt_id)
            )
            await session.commit()

            try:
                await conn.send(
                    MessageType.DISPATCH_TASK.value,
                    {
                        "run_id": run.id,
                        "attempt_id": attempt_id,
                        "snapshot_id": run.snapshot_id,
                        "command": run.command,
                        "working_dir": run.working_dir,
                        "env": json.loads(run.env) if run.env else {},
                        "timeout_seconds": 3600,
                    },
                    run_id=run.id,
                )
                return True
            except Exception as e:
                logger.error(f"Failed to dispatch task {run_id} to {host_id}: {e}")
                return False
                return False

    async def request_probes(self, host_id: str, probes: list[str]) -> bool:
        """Request worker to run environment probes."""
        conn = self.get_connection(host_id)
        if not conn:
            return False

        try:
            await conn.send(MessageType.PROBE_REQUEST.value, {"probes": probes})
            return True
        except Exception as e:
            logger.error(f"Failed to request probes from {host_id}: {e}")
            return False


from hearth_controller.config import settings

gateway = WorkerGateway(auto_approve=settings.worker_auto_approve)


async def handle_worker_message(conn: WorkerConnection, message: dict) -> None:
    """Process a message from an authenticated worker."""
    msg_type = message.get("type")
    payload = message.get("payload", {})
    run_id = message.get("run_id")
    host_id = conn.host_id

    # DEBUG: Log all received message types
    logger.info(f"[DEBUG] Received message type: {msg_type} from host {host_id}")

    try:
        async with async_session_maker() as db:
            if msg_type == MessageType.HEARTBEAT.value:
                conn.last_heartbeat = datetime.now(timezone.utc)
                host = await db.get(Host, conn.host_id)
                if host:
                    host.last_heartbeat_at = datetime.now(timezone.utc)

                now = datetime.now(timezone.utc)
                metrics = await db.get(HostMetricsLatest, conn.host_id)
                if not metrics:
                    metrics = HostMetricsLatest(host_id=conn.host_id)
                    db.add(metrics)

                metrics.updated_at = now

                # Only update fields that are present and valid in payload (prevents null overwrites)
                # Numeric fields: must be present and not None
                if "memory_used_gb" in payload and payload["memory_used_gb"] is not None:
                    metrics.memory_used_gb = payload["memory_used_gb"]
                if "memory_total_gb" in payload and payload["memory_total_gb"] is not None:
                    metrics.memory_total_gb = payload["memory_total_gb"]
                if "disk_used_gb" in payload and payload["disk_used_gb"] is not None:
                    metrics.disk_used_gb = payload["disk_used_gb"]
                if "disk_total_gb" in payload and payload["disk_total_gb"] is not None:
                    metrics.disk_total_gb = payload["disk_total_gb"]
                if "cpu_percent" in payload and payload["cpu_percent"] is not None:
                    metrics.cpu_percent = payload["cpu_percent"]
                if "current_task_id" in payload:
                    metrics.current_run_id = payload["current_task_id"]

                # For list fields: present and is list means update (even if empty list)
                if "gpus" in payload and isinstance(payload["gpus"], list):
                    metrics.gpus_json = json.dumps(payload["gpus"])
                if "cached_snapshots" in payload and isinstance(payload["cached_snapshots"], list):
                    metrics.cached_snapshots_json = json.dumps(payload["cached_snapshots"])

                # SSH config for rsync fallback (string/int fields - allow None to clear)
                if "ssh_host" in payload:
                    metrics.ssh_host = payload["ssh_host"]
                if "ssh_port" in payload:
                    metrics.ssh_port = payload["ssh_port"]
                if "ssh_user" in payload:
                    metrics.ssh_user = payload["ssh_user"]
                if "snapshot_inbox_path" in payload and payload["snapshot_inbox_path"] is not None:
                    metrics.snapshot_inbox_path = payload["snapshot_inbox_path"]
                if "api_port" in payload and payload["api_port"] is not None:
                    metrics.api_port = payload["api_port"]

                # Observed remote address from WebSocket connection (controller-side)
                if conn.remote_addr:
                    metrics.observed_remote_addr = conn.remote_addr
                    metrics.observed_remote_port = conn.remote_port
                    metrics.observed_remote_at = now

                # START evidence latch: if heartbeat indicates worker is running a task,
                # latch started_at even if TASK_STARTED was lost (at-most-once protection)
                current_task_id = payload.get("current_task_id")
                current_attempt_id = payload.get("current_attempt_id")
                if current_task_id and current_attempt_id:
                    result = await db.execute(
                        update(Run)
                        .where(Run.id == current_task_id)
                        .where(Run.host_id == conn.host_id)
                        .where(Run.current_attempt_id == current_attempt_id)
                        .where(Run.status.in_(["dispatched", "accepted"]))
                        .where(Run.started_at.is_(None))
                        .values(
                            status="running",
                            started_at=datetime.now(timezone.utc),
                        )
                        .returning(Run.id)
                    )
                    latched_run = result.scalar_one_or_none()
                    if latched_run:
                        logger.info(
                            f"Latched started_at for run {current_task_id} via heartbeat "
                            f"(TASK_STARTED may have been lost)"
                        )
                        # Broadcast status change to frontend
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(
                            current_task_id, "running", conn.host_id
                        )

                await db.commit()
                await conn.send(MessageType.HEARTBEAT_ACK.value, {})

                # Broadcast persisted metrics snapshot to frontend clients
                # This ensures we always send complete data, even if heartbeat payload was partial
                client_gw = get_client_gateway()

                # Fetch the persisted metrics snapshot from database
                metrics_snapshot = await db.get(HostMetricsLatest, conn.host_id)

                broadcast_data = {}
                if metrics_snapshot:
                    broadcast_data = {
                        "cpu_percent": metrics_snapshot.cpu_percent,
                        "memory_used_gb": metrics_snapshot.memory_used_gb,
                        "memory_total_gb": metrics_snapshot.memory_total_gb,
                        "disk_used_gb": metrics_snapshot.disk_used_gb,
                        "disk_total_gb": metrics_snapshot.disk_total_gb,
                        "current_run_id": metrics_snapshot.current_run_id,
                        "gpus": json.loads(metrics_snapshot.gpus_json)
                        if metrics_snapshot.gpus_json
                        else None,
                        "cached_snapshots": json.loads(metrics_snapshot.cached_snapshots_json)
                        if metrics_snapshot.cached_snapshots_json
                        else None,
                    }

                await client_gw.broadcast_metrics(conn.host_id, broadcast_data)

            elif msg_type == MessageType.PROBE_RESPONSE.value:
                host = await db.get(Host, conn.host_id)
                if host:
                    results = payload.get("results", [])
                    capabilities = {}
                    # Aliasing map: new probe names -> legacy capability keys
                    CAPABILITY_ALIASES = {
                        "python.version": "python",
                        "uv.version": "uv",
                        "nvidia.driver": "nvidia-smi",
                        "nvidia.gpu": "cuda",
                    }
                    for result in results:
                        probe_name = result.get("probe", "unknown")
                        if result.get("found"):
                            cap_value = {
                                "version": result.get("version"),
                                "path": result.get("path"),
                            }
                            capabilities[probe_name] = cap_value
                            # Add alias for legacy capability matching
                            if probe_name in CAPABILITY_ALIASES:
                                capabilities[CAPABILITY_ALIASES[probe_name]] = cap_value
                    host.capabilities = json.dumps(capabilities)
                    host.updated_at = datetime.now(timezone.utc)

                    await db.commit()
                    logger.info(
                        f"Updated capabilities for {conn.host_id}: {len(capabilities)} probes"
                    )

            elif msg_type == MessageType.TASK_ACCEPTED.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_ACCEPTED missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    # Transition dispatched -> accepted (worker accepted the task but hasn't started yet)
                    # Guard: verify attempt_id matches current dispatch attempt
                    result = await db.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .where(Run.status == "dispatched")
                        .where(Run.host_id == conn.host_id)
                        .where(Run.current_attempt_id == attempt_id)
                        .values(status="accepted", accepted_at=datetime.now(timezone.utc))
                        .returning(Run.id)
                    )
                    updated = result.scalar_one_or_none()
                    if updated:
                        await db.commit()
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(run_id, "accepted", conn.host_id)

            elif msg_type == MessageType.TASK_STARTED.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_STARTED missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    result = await db.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .where(Run.host_id == conn.host_id)
                        .where(Run.status.in_(["dispatched", "accepted"]))
                        .where(Run.current_attempt_id == attempt_id)
                        .where(Run.started_at.is_(None))
                        .values(
                            status="running",
                            started_at=datetime.now(timezone.utc),
                            work_path=payload.get("work_path"),
                            accepted_at=case(
                                (Run.status == "dispatched", datetime.now(timezone.utc)),
                                else_=Run.accepted_at,
                            ),
                        )
                        .returning(Run.id)
                    )
                    updated = result.scalar_one_or_none()
                    if updated:
                        await db.commit()
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(run_id, "running", conn.host_id)

            elif msg_type == MessageType.TASK_UPLOADING.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_UPLOADING missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    # Transition running -> uploading (worker is uploading results)
                    # Guard: verify attempt_id matches current dispatch attempt
                    result = await db.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .where(Run.host_id == conn.host_id)
                        .where(Run.status == "running")
                        .where(Run.current_attempt_id == attempt_id)
                        .values(status="uploading")
                        .returning(Run.id)
                    )
                    updated = result.scalar_one_or_none()
                    if updated:
                        await db.commit()
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(run_id, "uploading", conn.host_id)

            elif msg_type == MessageType.TASK_LOG.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_LOG missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    # Guard: verify attempt_id matches current dispatch attempt
                    result = await db.execute(
                        select(Run.id)
                        .where(Run.id == run_id)
                        .where(Run.host_id == conn.host_id)
                        .where(Run.current_attempt_id == attempt_id)
                    )
                    run_exists = result.scalar_one_or_none()
                    if run_exists:
                        log_entry = RunLog(
                            run_id=run_id,
                            stream=payload.get("stream", "stdout"),
                            content=payload.get("content", ""),
                        )
                        db.add(log_entry)
                        await db.commit()

            elif msg_type == MessageType.TASK_COMPLETED.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_COMPLETED missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    # Check if run was in canceling state - if so, log "cancel too late" but keep succeeded
                    run = await db.get(Run, run_id)
                    was_canceling = (
                        run
                        and run.host_id == conn.host_id
                        and run.current_attempt_id == attempt_id
                        and run.finished_at is None
                        and run.status == "canceling"
                    )

                    result = await db.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .where(Run.host_id == conn.host_id)
                        .where(
                            Run.status.in_(
                                ["dispatched", "accepted", "running", "uploading", "canceling"]
                            )
                        )
                        .where(Run.current_attempt_id == attempt_id)
                        .where(Run.finished_at.is_(None))
                        .values(
                            status="succeeded",
                            exit_code=payload.get("exit_code", 0),
                            finished_at=datetime.now(timezone.utc),
                        )
                        .returning(Run.id)
                    )
                    updated = result.scalar_one_or_none()
                    if updated:
                        await db.commit()
                        if was_canceling:
                            logger.info(f"Run {run_id} completed successfully (cancel too late)")
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(run_id, "succeeded", conn.host_id)

            elif msg_type == MessageType.TASK_FAILED.value:
                if run_id:
                    attempt_id = payload.get("attempt_id")

                    # Reject missing attempt_id explicitly
                    if not attempt_id:
                        logger.warning(
                            f"TASK_FAILED missing attempt_id for run {run_id} from host {conn.host_id}"
                        )
                        return

                    # Check if run is in canceling state - any failure while canceling = canceled
                    # This handles both signal exit codes and other failure modes during cancellation
                    exit_code = payload.get("exit_code")
                    run = await db.get(Run, run_id)
                    if (
                        run
                        and run.host_id == conn.host_id
                        and run.current_attempt_id == attempt_id
                        and run.finished_at is None
                        and run.status == "canceling"
                    ):
                        run.status = "canceled"
                        run.exit_code = exit_code
                        run.error_message = payload.get("error_message")
                        run.finished_at = datetime.now(timezone.utc)
                        await db.commit()
                        logger.info(
                            f"Run {run_id} canceled (TASK_FAILED while canceling, exit_code={exit_code})"
                        )
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(run_id, "canceled", conn.host_id)
                        return

                    result = await db.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .where(Run.host_id == conn.host_id)
                        .where(Run.status.in_(["dispatched", "accepted", "running", "uploading"]))
                        .where(Run.current_attempt_id == attempt_id)
                        .where(Run.finished_at.is_(None))
                        .values(
                            status="failed",
                            error_type=payload.get("error_type"),
                            error_message=payload.get("error_message"),
                            exit_code=exit_code,
                            finished_at=datetime.now(timezone.utc),
                        )
                        .returning(Run.id)
                    )
                    updated = result.scalar_one_or_none()
                    if updated:
                        await db.commit()
                        client_gw = get_client_gateway()
                        await client_gw.broadcast_run_status(
                            run_id, "failed", conn.host_id, payload.get("error_message")
                        )

            elif msg_type == MessageType.TASK_CANCELED.value:
                payload_obj = TaskCanceledPayload(**payload)
                run = await db.get(Run, payload_obj.run_id)
                if not run or run.current_attempt_id != payload_obj.attempt_id:
                    return
                if run.finished_at is not None:
                    return
                run.status = "canceled"
                run.finished_at = datetime.now(timezone.utc)
                run.exit_code = payload_obj.exit_code
                await db.commit()
                logger.info(f"Run {run.id} canceled by worker")
                client_gw = get_client_gateway()
                await client_gw.broadcast_run_status(payload_obj.run_id, "canceled", conn.host_id)

    except Exception as e:
        logger.exception(f"Error handling worker message: {e}")


def _major_version(ver: str) -> int | None:
    """Extract major version number from version string."""
    try:
        return int(ver.split(".", 1)[0])
    except Exception:
        return None


async def websocket_handler(websocket: WebSocket) -> None:
    """
    WebSocket handler for worker connections.

    Implements the full connection lifecycle:
    1. Accept connection
    2. Challenge-response authentication (Ed25519)
    3. Register with gateway
    4. Message receive loop
    5. Cleanup on disconnect
    """
    host_id: str | None = None
    conn: WorkerConnection | None = None

    await websocket.accept()

    try:
        # ---- Phase 1: Handshake (CHALLENGE -> HELLO -> WELCOME) ----
        async with async_session_maker() as db:
            identity_service = IdentityService(db, auto_approve=gateway.auto_approve)

            # Send challenge
            nonce = identity_service.generate_challenge()
            await websocket.send_json(
                {
                    "type": MessageType.CHALLENGE.value,
                    "payload": {"nonce": nonce},
                }
            )

            # Wait for HELLO with timeout
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HANDSHAKE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning("Handshake timeout waiting for HELLO")
                await websocket.close(code=status.WS_1002_PROTOCOL_ERROR)
                return

            # Validate payload size
            if len(raw) > MAX_PAYLOAD_SIZE:
                logger.warning(f"HELLO payload too large: {len(raw)} bytes")
                await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                return

            # Parse HELLO
            try:
                hello = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in HELLO message")
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                return

            if hello.get("type") != MessageType.HELLO.value:
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "bad_handshake",
                            "message": "Expected HELLO message",
                            "retryable": False,
                        },
                    }
                )
                await websocket.close(code=status.WS_1002_PROTOCOL_ERROR)
                return

            payload = hello.get("payload") or {}
            public_key = payload.get("public_key")
            signature = payload.get("signature")
            claims = payload.get("claims") or {}
            hardware = payload.get("hardware") or {}
            worker_proto = payload.get("protocol_version") or ""

            # Validate required fields
            if not public_key or not signature:
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "bad_handshake",
                            "message": "Missing public_key or signature in HELLO",
                            "retryable": False,
                        },
                    }
                )
                await websocket.close(code=status.WS_1002_PROTOCOL_ERROR)
                return

            # Protocol version check (major compatibility)
            if _major_version(worker_proto) != _major_version(PROTOCOL_VERSION):
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "incompatible_protocol",
                            "message": f"Worker protocol {worker_proto} incompatible with controller {PROTOCOL_VERSION}",
                            "retryable": False,
                        },
                    }
                )
                await websocket.close(code=status.WS_1002_PROTOCOL_ERROR)
                return

            # Verify signature and find/create host
            try:
                identity_service.verify_signature(public_key, nonce, signature)
                host, host_identity, is_new = await identity_service.find_or_create_host(
                    public_key_b64=public_key,
                    claims=claims,
                    hardware=hardware,
                )
                await db.commit()
            except InvalidSignatureError as e:
                await db.rollback()
                logger.warning(f"Authentication failed: {e}")
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "auth_failed",
                            "message": str(e),
                            "retryable": False,
                        },
                    }
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            except IdentityRevokedError as e:
                await db.rollback()
                logger.warning(f"Revoked identity attempted connection: {e}")
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "identity_revoked",
                            "message": str(e),
                            "retryable": False,
                        },
                    }
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            except IdentityError as e:
                await db.rollback()
                logger.error(f"Identity error during handshake: {e}")
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR.value,
                        "payload": {
                            "code": "identity_error",
                            "message": str(e),
                            "retryable": True,
                        },
                    }
                )
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                return

            host_id = str(host.id)
            conn = await gateway.register_connection(websocket, host_id, host.status)

            # Send WELCOME with connection parameters
            await websocket.send_json(
                {
                    "type": MessageType.WELCOME.value,
                    "payload": {
                        "host_id": host_id,
                        "status": host.status,
                        "protocol_version": PROTOCOL_VERSION,
                        "heartbeat_interval": HEARTBEAT_INTERVAL,
                        "probes": [
                            "python.version",
                            "uv.version",
                            "nvidia.driver",
                            "nvidia.gpu",
                            "os.release",
                        ],
                    },
                }
            )

            if is_new:
                logger.info(f"New worker registered: {host_id} (status: {host.status})")
            else:
                logger.info(f"Worker reconnected: {host_id}")

        # ---- Phase 1b: Request probes after handshake ----
        # Auto-request probes to detect worker capabilities
        # Probe names must match worker's BUILTIN_PROBES keys exactly
        await gateway.request_probes(
            host_id,
            ["python.version", "uv.version", "nvidia.driver", "nvidia.gpu", "os.release"],
        )

        # ---- Phase 2: Main receive loop ----
        while True:
            try:
                raw = await websocket.receive_text()

                # Validate payload size
                if len(raw) > MAX_PAYLOAD_SIZE:
                    if conn:
                        await conn.send_error(
                            "message_too_big", "Payload exceeds limit", retryable=False
                        )
                    await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                    return

                # Parse message
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    if conn:
                        await conn.send_error(
                            "invalid_json", "Could not parse JSON", retryable=True
                        )
                    continue

                # Validate message structure
                if not isinstance(message, dict) or "type" not in message:
                    if conn:
                        await conn.send_error(
                            "invalid_message", "Missing type field", retryable=True
                        )
                    continue

                # Handle message (isolated: don't disconnect on handler error)
                try:
                    await handle_worker_message(conn, message)
                except Exception as e:
                    logger.exception(f"Error handling message from {host_id}: {e}")
                    if conn:
                        await conn.send_error(
                            "internal_error",
                            "Controller failed to process message",
                            retryable=True,
                        )
                    # Continue processing next messages

            except WebSocketDisconnect:
                logger.info(f"Worker {host_id} disconnected normally")
                return

    except Exception as e:
        logger.exception(f"WebSocket connection error: {e}")
    finally:
        if host_id:
            await gateway.disconnect(host_id)
