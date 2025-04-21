import asyncio
from mongo_broadcaster import MongoChangeBroadcaster, BroadcasterConfig, CollectionConfig, HTTPCallbackChannel


async def main():
	http_channel = HTTPCallbackChannel(
		endpoint="http://localhost:8001/webhook",
		headers={"Authorization": "Bearer test123"}
	)

	config = BroadcasterConfig(
		mongo_uri="mongodb://localhost:27017",
		collections=[
			CollectionConfig(
				collection_name="orders",
				database_name="test"
			)
		]
	)

	broadcaster = MongoChangeBroadcaster(config)
	broadcaster.add_channel(http_channel)

	await http_channel.connect()
	await broadcaster.start()

	try:
		while True:
			await asyncio.sleep(1)
	except KeyboardInterrupt:
		await broadcaster.stop()


asyncio.run(main())
