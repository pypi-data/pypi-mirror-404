"""
WebSocket Connection Manager with Challenge-Response Authentication

Uses Ed25519 signatures for worker authentication instead of bearer tokens.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import websockets

from hearth_common.protocol.version import PROTOCOL_VERSION
from hearth_worker.config import settings
from hearth_worker.identity import IdentityManager, collect_claims, collect_hardware

if TYPE_CHECKING:
    from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connection to controller with Ed25519 authentication.

    Handshake flow:
    1. Connect to controller
    2. Receive CHALLENGE with nonce
    3. Sign nonce with Ed25519 private key
    4. Send HELLO with public_key, signature, claims, hardware
    5. Receive WELCOME with host_id, status, probes
    """

    def __init__(
        self,
        controller_url: str,
        identity_manager: IdentityManager,
        on_message: Callable[[dict[str, Any]], Any],
        on_connected: Callable[[], Any] | None = None,
    ):
        self.controller_url = controller_url
        self.identity = identity_manager
        self.on_message = on_message
        self.on_connected = on_connected

        self.ws: WebSocketClientProtocol | None = None
        self.host_id: str | None = None
        self.host_status: str | None = None
        self.heartbeat_interval: int = 30
        self.probes_to_run: list[str] = []

        self.last_seq = 0
        self._running = False
        self._reconnect_attempt = 0
        self._seq = 0
        self._send_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection and perform challenge-response handshake."""
        ws_url = f"{self.controller_url}/ws/worker"

        self.ws = await websockets.connect(
            ws_url,
            ping_interval=20,
            ping_timeout=10,
        )
        self._reconnect_attempt = 0

        # Step 1: Receive CHALLENGE
        response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
        data = json.loads(response)

        if data.get("type") == "error":
            raise ConnectionError(f"Connection failed: {data.get('payload', {}).get('message')}")

        if data.get("type") != "challenge":
            raise ConnectionError(f"Expected CHALLENGE, got {data.get('type')}")

        nonce = data.get("payload", {}).get("nonce")
        if not nonce:
            raise ConnectionError("CHALLENGE missing nonce")

        # Step 2: Sign nonce and send HELLO
        await self._send_hello(nonce)

        # Step 3: Receive WELCOME
        response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
        data = json.loads(response)

        if data.get("type") == "error":
            payload = data.get("payload", {})
            raise ConnectionError(
                f"Authentication failed: {payload.get('code')} - {payload.get('message')}"
            )

        if data.get("type") != "welcome":
            raise ConnectionError(f"Expected WELCOME, got {data.get('type')}")

        payload = data.get("payload", {})
        self.host_id = payload.get("host_id")
        self.host_status = payload.get("status")
        self.heartbeat_interval = payload.get("heartbeat_interval", 30)
        self.probes_to_run = payload.get("probes", [])

        # Save host_id for future reconnections
        if self.host_id:
            self.identity.save_host_id(self.host_id)

        logger.info(
            f"Connected to controller as {self.host_id} "
            f"(status: {self.host_status}, probes: {len(self.probes_to_run)})"
        )

        # Notify HearthAgent that connection is established
        if self.on_connected:
            await self.on_connected()

    async def _send_hello(self, nonce: str) -> None:
        """Sign nonce and send HELLO message."""
        signature = self.identity.sign_base64(nonce)
        public_key = self.identity.get_public_key_base64()
        claims = collect_claims()
        hardware = collect_hardware()

        hello = {
            "type": "hello",
            "payload": {
                "host_id": self.identity.get_host_id(),
                "public_key": public_key,
                "signature": signature,
                "protocol_version": PROTOCOL_VERSION,
                "claims": claims,
                "hardware": hardware,
            },
            "seq": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.ws.send(json.dumps(hello))

    async def run(self) -> None:
        """Main connection loop with automatic reconnection."""
        self._running = True

        while self._running:
            try:
                await self.connect()

                # Run probes if requested
                if self.probes_to_run:
                    await self._run_and_report_probes()

                # Start receive loop only - heartbeat is handled by WorkerSession
                await self._receive_loop()
            except websockets.ConnectionClosed:
                logger.warning("Connection closed")
                await self._handle_disconnect()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await self._handle_disconnect()

    async def _receive_loop(self) -> None:
        """Process incoming messages."""
        async for message in self.ws:
            data = json.loads(message)
            self.last_seq = data.get("seq", self.last_seq)

            msg_type = data.get("type")

            if msg_type == "heartbeat_ack":
                continue
            elif msg_type == "probe_request":
                probes = data.get("payload", {}).get("probes", [])
                if probes:
                    self.probes_to_run = probes
                    await self._run_and_report_probes()
            else:
                await self.on_message(data)

    async def _run_and_report_probes(self) -> None:
        """Run environment probes and report results."""
        if not self.probes_to_run:
            return

        try:
            from hearth_worker.probes import SecureProbeRunner

            runner = SecureProbeRunner()
            results = await runner.run_probes(self.probes_to_run)

            await self.send(
                {
                    "type": "probe_response",
                    "payload": {
                        "results": [r.to_dict() for r in results],
                    },
                }
            )
            logger.info(f"Reported {len(results)} probe results")
        except ImportError:
            logger.warning("Probes module not available, skipping")
        except Exception as e:
            logger.error(f"Failed to run probes: {e}")

    async def _handle_disconnect(self) -> None:
        """Handle disconnection with exponential backoff."""
        if not self._running:
            return

        delays = settings.reconnect_delays
        delay = delays[min(self._reconnect_attempt, len(delays) - 1)]
        self._reconnect_attempt += 1

        logger.info(f"Reconnecting in {delay}s (attempt {self._reconnect_attempt})")
        await asyncio.sleep(delay)

    async def send(self, message: dict) -> None:
        """Send a message to the controller with lock protection."""
        if self.ws:
            async with self._send_lock:
                self._seq += 1
                message["seq"] = self._seq
                message["timestamp"] = datetime.now(timezone.utc).isoformat()
                message["worker_id"] = self.host_id
                await self.ws.send(json.dumps(message))

    async def stop(self) -> None:
        """Stop the connection."""
        self._running = False
        if self.ws:
            await self.ws.close()
