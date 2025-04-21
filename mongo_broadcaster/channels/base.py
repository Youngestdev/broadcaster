from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseChannel(ABC):
    @abstractmethod
    async def connect(self):
        """Initialize connection"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass

    @abstractmethod
    async def send(self, recipient: str, message: Dict[str, Any]):
        """Send message to recipient"""
        pass
