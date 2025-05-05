import asyncio
import logging
from typing import Dict, Any, Tuple, Union
from datetime import datetime, timedelta

from fastapi import WebSocket
from mongo_broadcaster.utils import safe_json_dumps
from starlette.websockets import WebSocketDisconnect
from contextlib import suppress

from .base import BaseChannel

logger = logging.getLogger(__name__)

PING_INTERVAL = 60  # seconds


class WebSocketChannel(BaseChannel):
    def __init__(self, disconnect_on_timeout: bool = False, timeout: Union[int, None] = None):
        # Map client_id -> (websocket, ping_task, last_pong_time)
        self.active_connections: Dict[str, Tuple[WebSocket, asyncio.Task, datetime]] = {}
        self.lock = asyncio.Lock()
        self.disconnect_on_timeout = disconnect_on_timeout
        self.timeout = timeout

    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept a WebSocket connection and start a ping/pong monitor."""
        await websocket.accept()
        logger.info(f"[{client_id}] Connecting...")

        async with self.lock:
            old = self.active_connections.get(client_id)
            if old:
                old_ws, old_ping_task, _ = old
                logger.info(f"[{client_id}] Replacing existing connection.")
                with suppress(Exception):
                    await old_ws.close()
                old_ping_task.cancel()

            now = datetime.utcnow()
            ping_task = asyncio.create_task(self._send_pings(client_id))
            self.active_connections[client_id] = (websocket, ping_task, now)

        await self._listen_loop(client_id, websocket)

    async def _listen_loop(self, client_id: str, websocket: WebSocket):
        """Handle incoming messages (look for pong responses)."""
        try:
            while True:
                data = await websocket.receive_text()
                if data.strip().lower() == "pong":
                    async with self.lock:
                        if client_id in self.active_connections:
                            ws, task, _ = self.active_connections[client_id]
                            self.active_connections[client_id] = (ws, task, datetime.utcnow())
        except WebSocketDisconnect:
            logger.info(f"[{client_id}] Disconnected.")
        except Exception as e:
            logger.exception(f"[{client_id}] Error: {e}")
        finally:
            await self.disconnect(client_id)

    async def _send_pings(self, client_id: str):
        """Ping the client and enforce pong timeout."""
        try:
            while True:
                await asyncio.sleep(PING_INTERVAL)

                async with self.lock:
                    conn = self.active_connections.get(client_id)
                    if not conn:
                        return  # Client disconnected
                    websocket, _, last_pong = conn

                # Check if pong was received recently
                if datetime.utcnow() - last_pong > timedelta(seconds=self.timeout):
                    logger.warning(f"[{client_id}] Pong timeout.")
                    if self.disconnect_on_timeout:
                        await self.disconnect(client_id)
                        return

                try:
                    await websocket.send_text("ping")
                except Exception:
                    logger.warning(f"[{client_id}] Ping send failed. Disconnecting.")
                    await self.disconnect(client_id)
                    return
        except asyncio.CancelledError:
            pass

    async def disconnect(self, client_id: str):
        """Remove a connection and cancel ping monitor."""
        async with self.lock:
            entry = self.active_connections.pop(client_id, None)

        if entry:
            websocket, ping_task, _ = entry
            ping_task.cancel()
            with suppress(Exception):
                await websocket.close()
            logger.info(f"[{client_id}] Cleaned up.")

    async def send(self, recipient: str, message: Dict[str, Any]):
        """Send a message to a client if connection is valid."""
        async with self.lock:
            conn = self.active_connections.get(recipient)

        if conn:
            websocket, _, _ = conn
            try:
                await websocket.send_json(safe_json_dumps(message))
            except Exception as e:
                logger.warning(f"[{recipient}] Send failed: {e}")
                await self.disconnect(recipient)

    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients."""
        async with self.lock:
            connections = list(self.active_connections.items())

        for client_id, (websocket, _, _) in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                logger.warning(f"[{client_id}] Dead connection in broadcast.")
                await self.disconnect(client_id)
