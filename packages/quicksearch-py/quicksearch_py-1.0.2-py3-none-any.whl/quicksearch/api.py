from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List, Dict, Any
import os
import asyncio
from quicksearch.sync.manager import SyncManager
from quicksearch.core.searcher import QuickSearcher

app = FastAPI(title="QuickSearch API", description="High-performance scoped search")

# Path to our generated index
INDEX_PATH = ".quicksearch_index/mongo_bot_platform_bots"

from quicksearch.adapters.mongodb import MongoAdapter
from quicksearch.core.engine import SearchEngine

# Global searcher instance
searcher: Optional[QuickSearcher] = None

# Configuration - TODO: Move to a config file
MONGO_CONFIG = {
    "uri": "mongodb://localhost:27017/",
    "db": "bot_platform",
    "collection": "bots",
    "search_field": "name",
    "metadata_fields": ["owner_id", "org_id"],
    "id_field": "_id"
}

# Instantiate core components
sync_manager = SyncManager(INDEX_PATH)
adapter = MongoAdapter(MONGO_CONFIG)
engine = SearchEngine(INDEX_PATH, filterable_fields=["owner_id", "org_id"])

async def incremental_sync_loop():
    """Background task that runs forever to fetch new data."""
    while True:
        last_id = sync_manager.get_last_id()
        print(f"Checking for new bots since: {last_id}")
        
        # 1. Stream only new records
        # Note: You'll need to pass your Mongo config here
        new_records = adapter.stream_records(last_id=last_id)
        
        # 2. Add to index
        last_processed_id = await engine.index_records(new_records)
        
        # 3. Save progress
        if last_processed_id:
            sync_manager.save_checkpoint(last_processed_id)
            
        await asyncio.sleep(60)  # Wait 1 minute before checking again

@app.on_event("startup")
async def startup_event():
    """
    Mounts the index once when the server starts.
    Memory mapping ensures this is instant even with 5 crore rows.
    """
    global searcher
    if os.path.exists(INDEX_PATH):
        try:
            searcher = QuickSearcher(INDEX_PATH)
            print("🚀 Search Index Mounted and Ready!")
        except Exception as e:
            print(f"❌ Failed to mount index: {e}")
    else:
        print(f"⚠️ Warning: Index folder not found at {INDEX_PATH}")

    asyncio.create_task(incremental_sync_loop())

@app.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="The prefix to search for"),
    owner_id: Optional[str] = None,
    org_id: Optional[str] = None,
    limit: int = 10
):
    if not searcher:
        raise HTTPException(status_code=503, detail="Search index not ready")

    # Build the 'Scoped' filters dynamically
    filters = {}
    if owner_id:
        filters["owner_id"] = owner_id
    if org_id:
        filters["org_id"] = org_id

    # The actual high-speed lookup
    results = searcher.search(user_query=q, filters=filters, limit=limit)
    
    return {
        "status": "success",
        "count": len(results),
        "data": results
    }