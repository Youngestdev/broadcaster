import asyncio
from mongo_broadcaster import MongoChangeBroadcaster, BroadcasterConfig, CollectionConfig, DatabaseChannel


async def main():
	db_channel = DatabaseChannel(
		mongo_uri="mongodb://localhost:27017",
		database="change_logs",
		collection="events"
	)

	config = BroadcasterConfig(
		mongo_uri="mongodb://localhost:27017",
		collections=[
			CollectionConfig(
				collection_name="products",
				database_name="test"
			)
		]
	)

	broadcaster = MongoChangeBroadcaster(config)
	broadcaster.add_channel(db_channel)

	await db_channel.connect()
	await broadcaster.start()

	try:
		while True:
			await asyncio.sleep(1)
	except KeyboardInterrupt:
		await broadcaster.stop()


asyncio.run(main())
