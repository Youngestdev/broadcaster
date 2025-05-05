import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any
from .base import BaseChannel


class DatabaseChannel(BaseChannel):
    def __init__(self, mongo_uri: str, database: str, collection: str):
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.collection = None

    async def connect(self):
        """Initialize MongoDB connection"""
        self.client = AsyncIOMotorClient(self.mongo_uri)
        self.collection = self.client[self.database_name][self.collection_name]

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    async def send(self, recipient: str, message: Dict[str, Any]):
        """Save message to database"""
        if self.collection is None:
            raise RuntimeError("Database connection not established")

        document = {
            "recipient": recipient,
            "message": message,
            "timestamp": datetime.datetime.utcnow()
        }
        await self.collection.insert_one(document)

    async def broadcast(self, message: Dict[str, Any]):
        """Save broadcast message to database"""
        document = {
            "message": message,
            "timestamp": datetime.datetime.utcnow(),
            "broadcast": True
        }
        await self.collection.insert_one(document)
