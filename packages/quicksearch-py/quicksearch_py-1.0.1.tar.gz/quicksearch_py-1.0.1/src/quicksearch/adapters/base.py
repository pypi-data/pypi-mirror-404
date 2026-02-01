from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator

class BaseAdapter(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connection to the database.
        config: Dictionary containing URI, DB name, etc.
        """
        pass

    @abstractmethod
    async def stream_records(self, last_id: Optional[Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields records one by one to handle millions of rows without RAM spikes.
        Expected format: 
        {
            "id": str, 
            "text": str, 
            "metadata": Dict[str, Any]
        }
        """
        yield {}


    @abstractmethod
    def get_identifier(self) -> str:
        """
        Returns a unique string for this adapter (e.g., 'mongo_prod_bots').
        Used to name the local index folder.
        """
        pass