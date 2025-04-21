from fastapi import WebSocket
from typing import Dict, Any, List
from .base import BaseChannel


class WebSocketChannel(BaseChannel):
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Register a new websocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        """Remove a websocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send(self, recipient: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if recipient in self.active_connections:
            try:
                await self.active_connections[recipient].send_json(message)
            except Exception as e:
                await self.disconnect(recipient)
                raise e

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients"""
        for connection in list(self.active_connections.values()):
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                client_id = next(
                    (k for k, v in self.active_connections.items()
                     if v == connection), None)
                if client_id:
                    await self.disconnect(client_id)
