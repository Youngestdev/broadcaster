import json
import redis.asyncio as aioredis
from typing import Dict, Any
from .base import BaseChannel


class RedisPubSubChannel(BaseChannel):
    def __init__(self, redis_uri: str, channel_prefix: str = "mongo_change:"):
        self.redis_uri = redis_uri
        self.channel_prefix = channel_prefix
        self.redis = None

    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(self.redis_uri)

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    async def send(self, recipient: str, message: Dict[str, Any]):
        """Publish message to recipient-specific channel"""
        channel = f"{self.channel_prefix}{recipient}"
        await self.redis.publish(channel, json.dumps(message))

    async def broadcast(self, message: Dict[str, Any]):
        """Publish message to broadcast channel"""
        channel = f"{self.channel_prefix}broadcast"
        await self.redis.publish(channel, json.dumps(message))
