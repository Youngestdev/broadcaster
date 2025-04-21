from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChangeStreamConfig(BaseModel):
    """Configuration for MongoDB change stream"""
    pipeline: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {'$match': {'operationType': {'$in': ['insert', 'update']}}}
            # add support for delete later -> this requires some other changes
        ]
    )
    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            'full_document': 'updateLookup',
            'full_document_before_change': 'whenAvailable'
        }
    )


class CollectionConfig(BaseModel):
    """Configuration for a specific collection"""
    collection_name: str
    database_name: Optional[str] = None
    change_stream_config: ChangeStreamConfig = Field(default_factory=ChangeStreamConfig)
    fields_to_watch: List[str] = Field(default_factory=list)
    recipient_identifier: Optional[str] = None  # Field path to identify recipient (e.g., "owner.id")


class BroadcasterConfig(BaseModel):
    """Main configuration for the broadcaster"""
    mongo_uri: str
    collections: List[CollectionConfig]
    default_database: Optional[str] = None


class ChangeEvent(BaseModel):
    """Standardized change event model"""
    operation: str  # 'insert'|'update'
    collection: str
    document_id: str
    data: dict
    timestamp: float
    namespace: Optional[str] = None
    recipient: Optional[str] = Field(
        None,
        description="Target recipient ID if available (for directed messaging)"
    )
