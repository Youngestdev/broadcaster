import asyncio
from mongo_broadcaster import MongoChangeBroadcaster, BroadcasterConfig, CollectionConfig, RedisPubSubChannel


async def main():
	redis_channel = RedisPubSubChannel(
		redis_uri="redis://localhost:6379"
	)

	config = BroadcasterConfig(
		mongo_uri="mongodb://localhost:27017",
		collections=[
			CollectionConfig(
				collection_name="inventory",
				database_name="test",
				recipient_identifier="fullDocument.warehouse_id"
			)
		]
	)

	broadcaster = MongoChangeBroadcaster(config)
	broadcaster.add_channel(redis_channel)

	await redis_channel.connect()
	await broadcaster.start()

	try:
		while True:
			await asyncio.sleep(1)
	except KeyboardInterrupt:
		await broadcaster.stop()


asyncio.run(main())
