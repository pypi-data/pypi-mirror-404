import json
import os
from typing import Optional
from ..logging_config import get_logger
from ..exceptions import CheckpointError

logger = get_logger("sync_manager")


class SyncManager:
    def __init__(self, index_path: str):
        """
        Initialize sync manager with checkpoint file path.
        
        Args:
            index_path: Path to the index directory
        """
        self.index_path = index_path
        self.checkpoint_path = os.path.join(index_path, "checkpoint.json")
        
        # Ensure index directory exists
        try:
            os.makedirs(index_path, exist_ok=True)
            logger.debug(f"Index directory ensured at {index_path}")
        except OSError as e:
            logger.error(f"Failed to create index directory: {e}")
            raise CheckpointError(f"Cannot create index directory: {e}")

    def get_checkpoint(self) -> dict:
        """
        Read the last checkpoint from disk.
        
        Returns:
            Checkpoint dict with 'val' and 'type' keys
            
        Raises:
            CheckpointError: If checkpoint file is corrupted
        """
        if not os.path.exists(self.checkpoint_path):
            logger.debug("No checkpoint file found, starting fresh")
            return {"val": None, "type": "id"}
        
        try:
            with open(self.checkpoint_path, "r") as f:
                checkpoint = json.load(f)
                logger.debug(f"Loaded checkpoint: {checkpoint}")
                return checkpoint
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted checkpoint file, resetting: {e}")
            # Backup corrupted file
            try:
                backup_path = f"{self.checkpoint_path}.corrupted"
                os.rename(self.checkpoint_path, backup_path)
                logger.info(f"Backed up corrupted checkpoint to {backup_path}")
            except OSError:
                pass
            return {"val": None, "type": "id"}
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to read checkpoint file: {e}")
            raise CheckpointError(f"Cannot read checkpoint: {e}")

    def save_checkpoint(self, value, pointer_type="id"):
        """
        Save checkpoint to disk.
        
        Args:
            value: Checkpoint value (ObjectId or timestamp)
            pointer_type: Type of checkpoint ('id' or 'time')
            
        Raises:
            CheckpointError: If checkpoint cannot be written
        """
        try:
            # Write to temp file first, then rename (atomic operation)
            temp_path = f"{self.checkpoint_path}.tmp"
            with open(temp_path, "w") as f:
                json.dump({"val": str(value), "type": pointer_type}, f)
            
            # Atomic rename
            os.replace(temp_path, self.checkpoint_path)
            logger.debug(f"Saved checkpoint: {value} ({pointer_type})")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointError(f"Cannot save checkpoint: {e}")