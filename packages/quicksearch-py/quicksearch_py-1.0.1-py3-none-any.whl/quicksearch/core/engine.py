import os
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, ID, TEXT, KEYWORD
from whoosh.analysis import NgramWordAnalyzer
from whoosh.qparser import QueryParser
from typing import List, Dict, Any, Optional
from ..logging_config import get_logger

logger = get_logger("search_engine")

class SearchEngine:
    def __init__(
        self, 
        index_path: str, 
        filterable_fields: List[str],
        limitmb: int = 2048,  # RAM in MB for indexing buffer
        procs: int = None,    # CPU cores (None = auto-detect)
        batch_size: int = 1000  # Documents to batch before writing
    ):
        self.index_path = index_path
        self.filterable_fields = filterable_fields
        self.limitmb = limitmb
        self.batch_size = batch_size
        
        # Auto-detect CPU cores if not specified
        if procs is None:
            import sys
            import os
            # Use 1 core on Windows to avoid lock issues, otherwise use all cores
            self.procs = 1 if sys.platform == 'win32' else os.cpu_count()
        else:
            self.procs = procs
        
        # 1. Define the Schema
        # NgramWordAnalyzer(minsize=2) allows searching 'Cy' to find 'Cyber'
        self.analyzer = NgramWordAnalyzer(minsize=2, maxsize=20)
        
        # We dynamically build the schema based on user-defined filters
        schema_fields = {
            "id": ID(stored=True, unique=True),
            "text": TEXT(stored=True, analyzer=self.analyzer),
        }
        
        # Add metadata filters as non-analyzed KEYWORD fields for speed
        for field in filterable_fields:
            schema_fields[field] = KEYWORD(stored=True)
            
        self.schema = Schema(**schema_fields)

    def _initialize_index(self):
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
            return create_in(self.index_path, self.schema)
        return open_dir(self.index_path)

    async def index_records(self, record_stream, total_docs=None):
        """
        Index records with progress tracking and optimized batch performance.
        
        Args:
            record_stream: Async generator of records
            total_docs: Optional total document count for progress bar
        """
        import sys
        from tqdm.asyncio import tqdm
        
        # First, collect all records to avoid creating empty index files
        all_records = []
        last_val = None
        strategy = "id"
        
        # Create progress bar for collection
        pbar = tqdm(
            total=total_docs,
            desc="📥 Indexing",
            unit=" docs",
            unit_scale=True,
            colour="green",
            dynamic_ncols=True
        )
        
        try:
            async for record in record_stream:
                all_records.append({
                    "id": record["id"],
                    "text": record["text"],
                    **record.get("metadata", {})
                })
                
                last_val = record.get("checkpoint_val")
                strategy = record.get("pointer_type", "id")
                pbar.update(1)
            
            pbar.close()
            
            # If no records, return early WITHOUT creating a writer
            if len(all_records) == 0:
                print("✨ No new records to index.")
                return None
            
            # Now open writer and write all records in batches
            ix = self._initialize_index()
            writer = ix.writer(procs=self.procs, limitmb=self.limitmb, multisegment=True)
            
            count = 0
            for i in range(0, len(all_records), self.batch_size):
                batch = all_records[i:i + self.batch_size]
                for doc in batch:
                    writer.update_document(**doc)
                count += len(batch)

            print(f"💾 Committing {count:,} records to disk... (Please wait)")
            writer.commit(optimize=True)  # Optimize index during commit
            print(f"✅ Index updated successfully! ({count:,} documents)")
            
            return {
                "last_val": last_val,
                "count": count,
                "strategy": strategy
            }

        except Exception as e:
            if 'pbar' in locals():
                pbar.close()
            if 'writer' in locals():
                try:
                    writer.cancel()
                except:
                    pass  # Writer might already be closed
            
            # Handle specific errors
            from whoosh.index import LockError
            if isinstance(e, LockError):
                logger.error("Index is locked by another process")
                print(f"❌ Index Locked: Another process is using the index. Please try again.")
            elif isinstance(e, OSError):
                logger.error(f"Disk I/O error: {e}")
                print(f"❌ Disk Error: {e}. Check disk space and permissions.")
            else:
                logger.error(f"Indexing failed: {e}")
                print(f"❌ Indexing Failed: {e}")
            
            import traceback
            traceback.print_exc()
            return None