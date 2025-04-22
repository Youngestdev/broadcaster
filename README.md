# MongoDB Change Broadcaster

[![PyPI Version](https://img.shields.io/pypi/v/mongo-broadcaster.svg)](https://pypi.org/project/mongo-broadcaster/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mongo-broadcaster)](https://pypi.org/project/mongo-broadcaster/)

A real-time change stream broadcaster for MongoDB, supporting multiple delivery channels (WebSocket, Redis, HTTP, etc.) with extensible architecture.

> Read the blog post on the
> implementation [here](https://blog.youngest.dev/read/introducing-mongo-broadcaster-a-multi-channel-mongo-db-change-stream-processor).
>
> ![Building a Versatile Data Streaming System with Broadcaster Package](https://res.cloudinary.com/doqqbfgk4/image/upload/v1745271783/_-_visual_selection_1_krsv1z.png)

## Features

- 📡 Listen to MongoDB change streams
- 🚀 Built-in channels: WebSocket, Redis, HTTP, and Database Logging
- 🔌 Extensible architecture for custom channels
- ⚡ Async-first implementation
- 🛠️ Configurable pipelines and filtering

## Installation

```console
pip install mongo-broadcaster

# Optional dependencies for specific channels:
pip install mongo_broadcaster[fastapi]  # WebSocket
pip install mongo_broadcaster[redis]    # Redis Pub/Sub support
```

## Basic Usage

```python
from mongo_broadcaster import (
    MongoChangeBroadcaster,
    BroadcasterConfig,
    CollectionConfig
)
from mongo_broadcaster.channels import WebSocketChannel

# Initialize with MongoDB connection
config = BroadcasterConfig(
    mongo_uri="mongodb://localhost:27017",
    collections=[
        CollectionConfig(
            collection_name="users",
            fields_to_watch=["name", "email"],
            recipient_identifier="fullDocument._id"
        )
     ]
)

broadcaster = MongoChangeBroadcaster(config)
broadcaster.add_channel(WebSocketChannel())

# Start listening (typically in your app startup)
await broadcaster.start()
```

## Built-in Channels

| Channel               | Description               | Ideal For                |
|-----------------------|---------------------------|--------------------------|
| `WebSocketChannel`    | Real-time browser updates | Live dashboards          |
| `RedisPubSubChannel`  | Pub/Sub messaging         | Microservices            |
| `HTTPCallbackChannel` | Webhook notifications     | Third-party integrations |
| `DatabaseChannel`     | Persistent change logging | Audit trails             |

## Extending with Custom Channels

Implement your own channel by subclassing `BaseChannel`:

```python
from mongo_broadcaster.channels.base import BaseChannel
from typing import Any, Dict


class CustomMQTTChannel(BaseChannel):
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.client = None

    async def connect(self):
	"""Initialize your connection"""
	self.client = await setup_mqtt_client(self.broker_url)

    async def send(self, recipient: str, message: Dict[str, Any]):
	"""Send to specific recipient"""
	await self.client.publish(f"changes/{recipient}", message)

    async def broadcast(self, message: Dict[str, Any]):
	"""Send to all subscribers"""
	await self.client.publish("changes/all", message)

    async def disconnect(self):
	"""Clean up resources"""
	await self.client.disconnect()

# Usage:
broadcaster.add_channel(CustomMQTTChannel("mqtt://localhost"))
```

## Configuration Options

### CollectionConfig

```python
CollectionConfig(
    collection_name: str,
    database_name: Optional[str] = None,
	# Fields to include in change events
    fields_to_watch: List[str] = [],
	# Dot-notation path to identify recipients (e.g., "fullDocument._id")
    recipient_identifier: Optional[str] = None,
	# MongoDB change stream options
    change_stream_config: ChangeStreamConfig = ChangeStreamConfig()
)
```

## Examples

### FastAPI WebSocket Endpoint

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()
ws_channel = WebSocketChannel()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await ws_channel.connect(client_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
	await ws_channel.disconnect(client_id)
```

Please see the [examples](https://github.com/Youngestdev/broadcaster/tree/main/mongo_broadcaster/examples) folder for
more.

## Contributing

To add new channels:

1. Create a subclass of `BaseChannel`
2. Implement required methods:
  - `connect()`
  - `send()`
  - `broadcast()`
  - `disconnect()`
3. Submit a PR!

## License

MIT

## TODO

- [ ] Write tests
