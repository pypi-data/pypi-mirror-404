from typing import Dict, Any, List, Optional
from .engine import SearchEngine
from .searcher import QuickSearcher
from ..sync.manager import SyncManager

class QuickSearch:
    def __init__(
        self, 
        adapter, 
        index_path: str, 
        filterable_fields: List[str],
        limitmb: int = 2048,      # RAM for indexing (MB)
        procs: int = None,        # CPU cores (None = auto)
        batch_size: int = 1000    # Batch size for writes
    ):
        self.adapter = adapter
        self.index_path = index_path
        
        # Internal components with performance config
        self.engine = SearchEngine(
            index_path, 
            filterable_fields,
            limitmb=limitmb,
            procs=procs,
            batch_size=batch_size
        )
        self.sync_mgr = SyncManager(index_path)
        self._searcher = None # Lazy loaded

    async def sync(self):
        checkpoint = self.sync_mgr.get_checkpoint()
        
        # Stream records from adapter
        record_stream = self.adapter.stream_records(checkpoint)
        
        # Extract total count from first record, then re-yield all records
        async def stream_with_total():
            total = None
            async for record in record_stream:
                if total is None:
                    total = record.get("total_count")
                yield record, total
        
        # Collect records and total
        total_docs = None
        async def final_stream():
            nonlocal total_docs
            async for record, total in stream_with_total():
                if total_docs is None:
                    total_docs = total
                yield record
        
        # Pass to engine with total count
        result = await self.engine.index_records(final_stream(), total_docs=total_docs)
        
        if result and result['count'] > 0:
            self.sync_mgr.save_checkpoint(result['last_val'], result['strategy'])
            return result
        
        return None

    def search(self, query: str, filters: dict = None, limit: int = 10, fuzzy: bool = False):
        """
        Search the index.
        :param fuzzy: If True, uses Levenshtein distance to find typos. 
                      Warning: Slower on very large datasets.
        """
        if not self._searcher:
            self._searcher = QuickSearcher(self.index_path)
            
        return self._searcher.search(query, filters=filters, limit=limit, fuzzy=fuzzy)


    def push(self, record: Dict[str, Any]):
        """
        Push a single record into the index immediately.
        Useful for real-time updates when a new bot is created.
        """
        # We use a context manager to ensure the writer locks and unlocks quickly
        with self.engine.ix.writer() as writer:
            doc_data = {
                "id": str(record["id"]),
                "text": str(record["text"]),
                **record.get("metadata", {})
            }
            writer.update_document(**doc_data)
        
        # Clear the searcher cache so the next search sees the new data
        self._searcher = None 
        return True