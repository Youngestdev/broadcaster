import asyncio
import logging
from typing import List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from .models import BroadcasterConfig, CollectionConfig
from .channels.base import BaseChannel
from .exceptions import ChannelNotConnectedError
from .utils import (
	ChangeEvent,
	format_change_event,
	validate_mongo_connection,
	backoff_handler
)

logger = logging.getLogger(__name__)


class MongoChangeBroadcaster:
	def __init__(self, config: BroadcasterConfig):
		self.config = config
		self.mongo_client: Optional[AsyncIOMotorClient] = None
		self.channels: List[BaseChannel] = []
		self._running = False
		self._tasks: List[asyncio.Task] = []

	async def _initialize_connection(self):
		"""Validate and establish MongoDB connection"""
		if not validate_mongo_connection(self.config.mongo_uri):
			raise ConnectionError("Invalid MongoDB connection URI")
		self.mongo_client = AsyncIOMotorClient(self.config.mongo_uri)

	def add_channel(self, channel: BaseChannel):
		"""Register an output channel"""
		self.channels.append(channel)

	async def start(self):
		"""Start all change stream watchers"""
		if not self.channels:
			raise ChannelNotConnectedError("No output channels configured")

		await self._initialize_connection()
		self._running = True

		for collection_config in self.config.collections:
			task = asyncio.create_task(
				self._watch_collection_with_retry(collection_config)
			)
			self._tasks.append(task)

	def _has_watched_field_changed(self, change: dict, fields: List[str]) -> bool:
		"""Check if any of the watched fields changed"""
		updated_fields = change.get("updateDescription", {}).get("updatedFields", {})

		for field in fields:
			if field in updated_fields:
				return True
		return False

	async def _watch_collection_with_retry(self, config: CollectionConfig):
		"""Wrapper with exponential backoff for resiliency"""
		from tenacity import retry, stop_after_attempt, wait_exponential

		@retry(
			stop=stop_after_attempt(3),
			wait=wait_exponential(multiplier=1, min=4, max=10),
			before_sleep=backoff_handler
		)
		async def _watch():
			await self._watch_collection(config)

		await _watch()

	async def _watch_collection(self, config: CollectionConfig):
		"""Monitor a single collection for changes"""
		db_name = config.database_name or self.config.default_database
		if not db_name:
			raise ValueError("Database name must be specified")

		db = self.mongo_client[db_name]
		collection = db[config.collection_name]

		try:
			async with collection.watch(
					pipeline=config.change_stream_config.pipeline,
					**config.change_stream_config.options
			) as change_stream:
				async for change in change_stream:
					if not self._running:
						break
					await self._process_change(change, config)

		except asyncio.CancelledError:
			logger.info(f"Stopped watching {config.collection_name}")
		except Exception as e:
			logger.error(f"Error watching {config.collection_name}: {str(e)}")
			raise

	def _extract_nested_field(self, doc: dict, field_path: str) -> Optional[Any]:
		"""Safely extract nested fields like 'owner.id'"""
		value = doc

		for key in field_path.split('.'):
			value = doc.get(key, {})
			if not value:
				continue
		return value

	async def _process_change(self, change: dict, config: CollectionConfig):
		"""Process and distribute a change event"""
		try:
			# Skip if none of the watched fields changed (for update events)
			if change.get("operationType") == "update" and config.fields_to_watch:
				if not self._has_watched_field_changed(change, config.fields_to_watch):
					return  # Skip processing

			# Extract recipient if configured
			recipient = None
			if config.recipient_identifier:
				doc = change.get('fullDocument') or change.get('fullDocumentBeforeChange', {})
				recipient = self._extract_nested_field(doc, config.recipient_identifier)

			event = format_change_event(change, config)
			event.recipient = str(recipient) if recipient else None
			await self._send_to_channels(event)

		except Exception as e:
			logger.error(f"Error processing change: {str(e)}")

	async def _send_to_channels(self, event: ChangeEvent):
		"""Broadcast to all registered channels"""
		for channel in self.channels:
			try:
				if event.recipient:  # Targeted delivery
					await channel.send(event.recipient, event.dict())
				else:  # Broadcast
					await channel.broadcast(event.dict())
			except Exception as e:
				logger.error(f"Channel {type(channel).__name__} failed: {str(e)}")

	async def stop(self):
		"""Gracefully shutdown all watchers"""
		self._running = False
		for task in self._tasks:
			task.cancel()
		await asyncio.gather(*self._tasks, return_exceptions=True)
		if self.mongo_client:
			self.mongo_client.close()
