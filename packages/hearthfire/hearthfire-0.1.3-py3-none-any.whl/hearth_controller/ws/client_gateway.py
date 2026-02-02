"""
WebSocket Gateway for Frontend Client Connections

Provides real-time updates to frontend clients:
- host_status_change: Host online/offline status changes
- run_status_change: Run status transitions
- metrics_update: Real-time host metrics updates

Note: This implementation is for single-instance deployment.
For multi-instance, consider adding Redis PubSub for cross-instance broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, status

from hearth_controller.db.models import User
from hearth_controller.db.session import async_session_maker
from hearth_controller.services.auth import verify_token

logger = logging.getLogger(__name__)

# Configuration
SEND_TIMEOUT = 5.0  # seconds - timeout for sending to a client
MAX_CONCURRENT_SENDS = 100  # limit concurrent sends to prevent event loop overload


class ClientConnection:
    """Represents a connected frontend client."""

    def __init__(self, websocket: WebSocket, client_id: str) -> None:
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now(timezone.utc)
        self._failed = False  # Mark for cleanup on send failure

    async def send(self, event_type: str, payload: dict[str, Any]) -> None:
        """Send an event to this client."""
        message = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": uuid4().hex,
        }
        await self.websocket.send_json(message)


class ClientGateway:
    """
    WebSocket gateway for frontend clients.

    Manages client connections and broadcasts events to all connected clients.
    """

    def __init__(self) -> None:
        self._clients: dict[str, ClientConnection] = {}
        self._lock = asyncio.Lock()
        self._send_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SENDS)

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)

    async def register(self, websocket: WebSocket) -> ClientConnection:
        """Register a new client connection."""
        client_id = uuid4().hex
        connection = ClientConnection(websocket, client_id)

        async with self._lock:
            self._clients[client_id] = connection

        logger.info(f"Client {client_id} connected (total: {self.client_count})")
        return connection

    async def unregister(self, client_id: str) -> None:
        """Remove a client connection."""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]

        logger.info(f"Client {client_id} disconnected (total: {self.client_count})")

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        """
        Broadcast an event to all connected clients.

        - Uses semaphore to limit concurrent sends
        - Applies timeout to prevent slow clients from blocking
        - Marks failed clients for cleanup
        """
        if not self._clients:
            return

        async with self._lock:
            clients = list(self._clients.values())

        # Send to all clients concurrently with semaphore limiting
        tasks = [self._safe_send(client, event_type, payload) for client in clients]
        await asyncio.gather(*tasks)

        # Cleanup failed clients
        await self._cleanup_failed_clients()

    async def _safe_send(
        self, client: ClientConnection, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Send to a client with timeout and error handling."""
        async with self._send_semaphore:
            try:
                await asyncio.wait_for(
                    client.send(event_type, payload),
                    timeout=SEND_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Send timeout to client {client.client_id}, marking for cleanup")
                client._failed = True
            except Exception as e:
                logger.warning(f"Failed to send to client {client.client_id}: {e}")
                client._failed = True

    async def _cleanup_failed_clients(self) -> None:
        """Remove clients marked as failed."""
        async with self._lock:
            failed_ids = [cid for cid, client in self._clients.items() if client._failed]
            for client_id in failed_ids:
                client = self._clients.pop(client_id, None)
                if client:
                    try:
                        await client.websocket.close()
                    except Exception:
                        pass
                    logger.info(f"Cleaned up failed client {client_id}")

    async def broadcast_host_status(
        self, host_id: str, status: str, name: str | None = None
    ) -> None:
        """Broadcast host status change."""
        await self.broadcast(
            "host_status_change",
            {"host_id": host_id, "status": status, "name": name},
        )

    async def broadcast_run_status(
        self,
        run_id: str,
        status: str,
        host_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Broadcast run status change."""
        await self.broadcast(
            "run_status_change",
            {"run_id": run_id, "status": status, "host_id": host_id, "error": error},
        )

    async def broadcast_metrics(self, host_id: str, metrics: dict[str, Any]) -> None:
        """Broadcast host metrics update."""
        await self.broadcast(
            "metrics_update",
            {"host_id": host_id, "metrics": metrics},
        )


# Global singleton instance
_client_gateway: ClientGateway | None = None


def get_client_gateway() -> ClientGateway:
    """Get the global client gateway instance."""
    global _client_gateway
    if _client_gateway is None:
        _client_gateway = ClientGateway()
    return _client_gateway


async def client_websocket_handler(websocket: WebSocket) -> None:
    """
    Handle a frontend client WebSocket connection.

    This is the endpoint handler for /ws/client.

    Authentication: Requires a valid token via query parameter:
    - ws://host/ws/client?token=<jwt_token>
    """
    # Extract token from query parameters
    token = websocket.query_params.get("token")
    if token:
        token = token.strip()

    if not token:
        # Reject connection without token
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("Client connection rejected: missing token")
        return

    # Verify token before accepting connection
    user: User | None = None
    try:
        async with async_session_maker() as db:
            user = await verify_token(db, token)
    except Exception as e:
        logger.warning(f"Token verification error: {e}")

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("Client connection rejected: invalid token")
        return

    # Token valid, accept connection
    await websocket.accept()

    gateway = get_client_gateway()
    connection = await gateway.register(websocket)

    logger.info(f"Client {connection.client_id} authenticated as user {user.id}")

    try:
        # Send welcome message with user info
        await connection.send(
            "welcome",
            {
                "client_id": connection.client_id,
                "user_id": user.id,
                "role": user.role,
            },
        )

        # Keep connection alive, handle client messages
        while True:
            try:
                # Wait for client messages (ping only for now)
                data = await websocket.receive_text()
                message = json.loads(data)

                msg_type = message.get("type")

                if msg_type == "ping":
                    await connection.send("pong", {})
                # Future: add subscribe/unsubscribe for filtered events

            except json.JSONDecodeError:
                logger.warning(f"Client {connection.client_id} sent invalid JSON")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"Client {connection.client_id} error: {e}")
    finally:
        await gateway.unregister(connection.client_id)
