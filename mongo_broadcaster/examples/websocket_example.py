from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from mongo_broadcaster import MongoChangeBroadcaster, BroadcasterConfig, CollectionConfig, WebSocketChannel


@asynccontextmanager
async def lifespan(app: FastAPI):
	await broadcaster.start()

	yield
	await broadcaster.stop()


app = FastAPI(lifespan=lifespan)
websocket_channel = WebSocketChannel()

config = BroadcasterConfig(
	mongo_uri="mongodb://localhost:27017",
	collections=[
		CollectionConfig(
			collection_name="users",
			recipient_identifier="fullDocument._id",  # Send to user who owns the document
			database_name="test",
		),
		CollectionConfig(
			collection_name="notifications",
			# No recipient_identifier means broadcast to all
		)
	]
)

broadcaster = MongoChangeBroadcaster(config)
broadcaster.add_channel(websocket_channel)


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
	await websocket_channel.connect(user_id, websocket)
	try:
		while True:
			await websocket.receive_text()  # Keep connection alive
	except WebSocketDisconnect:
		await websocket_channel.disconnect(user_id)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="0.0.0.0", port=8000)
