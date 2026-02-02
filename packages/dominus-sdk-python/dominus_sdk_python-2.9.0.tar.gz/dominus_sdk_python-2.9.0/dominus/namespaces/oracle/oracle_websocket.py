"""
OracleWebSocket - WebSocket wrapper for Oracle streaming (INTERNAL)

Handles:
- First-message authentication (browser WS doesn't support headers)
- Binary frames for audio (NOT base64)
- JSON frames for control messages
- Ping/pong keepalive during IDLE
- Transcript parsing and callback firing

This module is INTERNAL and should NOT be exported publicly.
"""

import asyncio
import json
from typing import Callable, Optional
from dataclasses import dataclass

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None


@dataclass
class OracleWebSocketConfig:
    """Configuration for OracleWebSocket."""
    ping_interval_ms: int = 10000


class OracleWebSocket:
    """
    OracleWebSocket - Manages WebSocket connection to Oracle service.
    """

    def __init__(self, base_url: str, config: Optional[OracleWebSocketConfig] = None):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package is required for Oracle streaming. "
                "Install with: pip install websockets"
            )

        self._base_url = base_url
        self._config = config or OracleWebSocketConfig()
        self._ws: Optional[WebSocketClientProtocol] = None
        self._authenticated = False
        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_transcript: Optional[Callable[[str, bool, bool], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_close: Optional[Callable[[], None]] = None

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected and authenticated."""
        return (
            self._ws is not None
            and self._ws.open
            and self._authenticated
        )

    async def connect(self, user_token: str) -> None:
        """
        Connect to Oracle WebSocket endpoint with first-message auth.

        Args:
            user_token: User JWT for authentication

        Raises:
            Exception: If connection or authentication fails
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = self._build_websocket_url()

        try:
            self._ws = await websockets.connect(ws_url)
        except Exception as e:
            raise Exception(f"Failed to create WebSocket: {e}")

        # Send first-message auth
        auth_message = json.dumps({
            "type": "auth",
            "token": user_token,
        })
        await self._ws.send(auth_message)

        # Wait for ready message
        try:
            response = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
            data = json.loads(response)

            if data.get("type") == "ready":
                self._authenticated = True
                self._start_ping_interval()
                self._start_receive_loop()
            elif data.get("type") == "error":
                raise Exception(f"Authentication failed: {data.get('message')}")
            else:
                raise Exception(f"Unexpected response type: {data.get('type')}")

        except asyncio.TimeoutError:
            await self._ws.close()
            raise Exception("Authentication timeout")

    def send_binary(self, pcm_frame: bytes) -> None:
        """
        Send binary PCM audio frame.
        Only called by VADGate - NOT exposed publicly.

        Args:
            pcm_frame: Raw PCM audio data
        """
        if self._ws and self._ws.open and self._authenticated:
            asyncio.create_task(self._ws.send(pcm_frame))

    async def send_ping(self) -> None:
        """Send a ping message for keepalive."""
        if self._ws and self._ws.open and self._authenticated:
            await self._ws.send(json.dumps({"type": "ping"}))

    async def close(self) -> None:
        """Close the WebSocket connection gracefully."""
        self._stop_ping_interval()
        self._stop_receive_loop()

        if self._ws:
            # Send close message before closing
            if self._ws.open:
                try:
                    await self._ws.send(json.dumps({"type": "close"}))
                except Exception:
                    pass  # Ignore send errors during close

            await self._ws.close()
            self._ws = None

        self._authenticated = False

    def _build_websocket_url(self) -> str:
        """Build WebSocket URL from base URL."""
        # Replace http(s) with ws(s)
        if self._base_url.startswith("https"):
            ws_protocol = "wss"
            http_protocol = "https"
        else:
            ws_protocol = "ws"
            http_protocol = "http"

        return self._base_url.replace(http_protocol, ws_protocol) + "/api/oracle/stream"

    def _start_receive_loop(self) -> None:
        """Start the receive loop for incoming messages."""
        async def receive_loop():
            try:
                while self._ws and self._ws.open:
                    try:
                        message = await self._ws.recv()
                        await self._handle_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        break
            finally:
                self._authenticated = False
                if self.on_close:
                    self.on_close()

        self._receive_task = asyncio.create_task(receive_loop())

    def _stop_receive_loop(self) -> None:
        """Stop the receive loop."""
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None

    async def _handle_message(self, message) -> None:
        """Handle incoming WebSocket message."""
        # Binary messages are not expected from server (audio is one-way)
        if isinstance(message, bytes):
            return

        # Parse JSON message
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print("[OracleSDK] Received invalid JSON from server")
            return

        msg_type = data.get("type")

        if msg_type == "transcript":
            text = data.get("text", "")
            is_final = data.get("is_final", False)
            speech_final = data.get("speech_final", False)

            print(f"[OracleSDK] Transcript received: text={text[:40] if text else ''!r}, "
                  f"is_final={is_final}, speech_final={speech_final}")

            if self.on_transcript:
                self.on_transcript(text, is_final, speech_final)

        elif msg_type == "pong":
            # Keepalive response - no action needed
            pass

        elif msg_type == "error":
            error = Exception(data.get("message", "Unknown error"))
            if self.on_error:
                self.on_error(error)

        else:
            print(f"[OracleSDK] Unknown message type: {msg_type}")

    def _start_ping_interval(self) -> None:
        """Start ping interval for keepalive."""
        async def ping_loop():
            while True:
                await asyncio.sleep(self._config.ping_interval_ms / 1000.0)
                await self.send_ping()

        self._ping_task = asyncio.create_task(ping_loop())

    def _stop_ping_interval(self) -> None:
        """Stop ping interval."""
        if self._ping_task:
            self._ping_task.cancel()
            self._ping_task = None
