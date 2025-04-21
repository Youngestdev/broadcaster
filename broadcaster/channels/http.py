import aiohttp
from typing import Dict, Any
from .base import BaseChannel


class HTTPCallbackChannel(BaseChannel):
    def __init__(self, endpoint: str, headers: Dict[str, str] = None, timeout: int = 5):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def connect(self):
        """Create aiohttp session"""
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)

    async def disconnect(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def send(self, recipient: str, message: Dict[str, Any]):
        """Send HTTP POST request"""
        payload = {
            "recipient": recipient,
            "event": message
        }
        async with self.session.post(self.endpoint, json=payload) as response:
            if response.status >= 400:
                raise ValueError(f"HTTP request failed with status {response.status}")

    async def broadcast(self, message: Dict[str, Any]):
        """Send broadcast HTTP POST request"""
        async with self.session.post(self.endpoint, json={"event": message}) as response:
            if response.status >= 400:
                raise ValueError(f"HTTP request failed with status {response.status}")
