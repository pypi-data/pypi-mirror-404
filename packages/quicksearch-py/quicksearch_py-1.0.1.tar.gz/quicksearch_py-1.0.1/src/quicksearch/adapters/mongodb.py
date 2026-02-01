import motor.motor_asyncio
from typing import Any, Dict, Optional, AsyncGenerator
from .base import BaseAdapter
from bson import ObjectId
from datetime import datetime
import asyncio
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from ..logging_config import get_logger
from ..exceptions import ConnectionError as QSConnectionError

logger = get_logger("mongodb_adapter")


class MongoAdapter(BaseAdapter):
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MongoDB adapter with connection validation.
        
        Args:
            config: MongoDB configuration dict
            
        Raises:
            QSConnectionError: If connection to MongoDB fails
        """
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config['uri'],
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            self.db = self.client[config['db']]
            self.collection = self.db[config['collection']]
            self.search_field = config['search_field']
            self.metadata_fields = config.get('metadata_fields', [])
            self.id_field = config.get('id_field', '_id')
            
            logger.info(f"MongoDB adapter initialized for {config['db']}.{config['collection']}")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB adapter: {e}")
            raise QSConnectionError(f"Failed to connect to MongoDB: {e}")

    async def validate_connection(self):
        """
        Validate MongoDB connection.
        
        Raises:
            QSConnectionError: If connection validation fails
        """
        try:
            await self.client.admin.command('ping')
            logger.debug("MongoDB connection validated")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection validation failed: {e}")
            raise QSConnectionError(f"MongoDB connection failed: {e}")

    def get_identifier(self) -> str:
        return f"mongo_{self.db.name}_{self.collection.name}"

    async def stream_records(self, checkpoint: dict, max_retries: int = 3):
        """
        Stream records with optimized batch size and error handling.
        
        Args:
            checkpoint: Last sync checkpoint
            max_retries: Maximum number of retries for transient errors
            
        Yields:
            Record dictionaries with metadata
            
        Raises:
            QSConnectionError: If MongoDB connection fails after retries
        """
        # Validate connection before streaming
        await self.validate_connection()
        
        # Detect the best strategy
        last_val = checkpoint.get("val")
        pointer_type = checkpoint.get("type")

        # Determine if we can use updated_at
        try:
            sample = await self.collection.find_one()
            if not sample:
                logger.warning("Collection is empty")
                return
                
            has_updated_at = "updated_at" in sample
        except PyMongoError as e:
            logger.error(f"Failed to sample collection: {e}")
            raise QSConnectionError(f"Failed to query MongoDB: {e}")

        if has_updated_at:
            # Convert string checkpoint back to datetime for comparison
            if last_val and pointer_type == "time":
                try:
                    last_val = datetime.fromisoformat(last_val.replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid checkpoint timestamp, resetting: {e}")
                    last_val = None
            
            query = {"updated_at": {"$gt": last_val}} if last_val else {}
            sort_field = "updated_at"
            current_type = "time"
        else:
            # Fallback to incremental-only via _id
            if last_val and pointer_type == "id":
                try:
                    query = {"_id": {"$gt": ObjectId(last_val)}}
                except Exception as e:
                    logger.warning(f"Invalid checkpoint ObjectId, resetting: {e}")
                    query = {}
            else:
                query = {}
            sort_field = "_id"
            current_type = "id"

        # Get total count for progress tracking
        try:
            total_count = await self.collection.count_documents(query)
            logger.info(f"Found {total_count} records to sync")
        except PyMongoError as e:
            logger.error(f"Failed to count documents: {e}")
            total_count = None
        
        # Stream records with retry logic
        retry_count = 0
        cursor = self.collection.find(query).sort(sort_field, 1).batch_size(5000)
        
        try:
            async for doc in cursor:
                # Validate required fields exist
                if "_id" not in doc:
                    logger.warning("Document missing _id, skipping")
                    continue
                    
                if self.search_field not in doc:
                    logger.warning(f"Document {doc['_id']} missing search field '{self.search_field}', skipping")
                    continue
                
                yield {
                    "id": str(doc["_id"]),
                    "text": str(doc[self.search_field]),
                    "metadata": {f: doc.get(f) for f in self.metadata_fields},
                    "checkpoint_val": doc[sort_field],
                    "pointer_type": current_type,
                    "total_count": total_count
                }
                
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            if retry_count < max_retries:
                retry_count += 1
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Connection lost, retrying in {wait_time}s (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                # Retry by recursively calling stream_records
                async for record in self.stream_records(checkpoint, max_retries - retry_count):
                    yield record
            else:
                logger.error(f"Failed to stream records after {max_retries} retries: {e}")
                raise QSConnectionError(f"MongoDB connection failed after {max_retries} retries: {e}")
        except PyMongoError as e:
            logger.error(f"MongoDB error while streaming: {e}")
            raise QSConnectionError(f"Failed to stream records: {e}")
