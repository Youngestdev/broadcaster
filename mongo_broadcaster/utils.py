import logging
from typing import Any, Dict
from datetime import date, datetime

import json

from mongo_broadcaster.models import ChangeEvent, CollectionConfig

logger = logging.getLogger(__name__)


def validate_mongo_connection(uri: str) -> bool:
    """Verify MongoDB connection is available"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(uri)
        client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False


def format_change_event(change: Dict[str, Any], config: CollectionConfig) -> ChangeEvent:
    """Transform raw MongoDB change stream event"""
    return ChangeEvent(
        operation=change['operationType'],
        collection=change['ns']['coll'],
        document_id=str(change['documentKey']['_id']),
        data=extract_fields(change, getattr(config, 'fields_to_watch', [])),
        timestamp=change['clusterTime'].time,
        namespace=change['ns']['db'],
        recipient=None
    )


def extract_fields(change: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """Extract specific fields from change stream data, supporting insert and update operations."""
    operation = change.get("operationType")
    result = {}

    if operation == "insert":
        source = change.get("fullDocument", {})
    elif operation == "update":
        source = change.get("updateDescription", {}).get("updatedFields", {})
    else:
        source = {}

    for field in fields:
        keys = field.split(".")
        value = source
        try:
            for key in keys:
                value = value.get(key, {})
            if value != {} and value is not None:
                result[field] = value
        except AttributeError:
            continue

    return result


def backoff_handler(details):
    """Exponential backoff for connection retries"""
    logger.warning(
        f"Retrying in {details['wait']:.1f} seconds after "
        f"{details['tries']} tries calling {details['target']}"
    )


def safe_json_dumps(data: Any) -> str:
    """Serialize data to JSON with datetime support."""

    def default(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    return json.dumps(data, default=default)
