import asyncio
import click
from quicksearch.adapters.mongodb import MongoAdapter
from quicksearch.core.engine import SearchEngine

@click.group()
def cli():
    """QuickSearch-Py: High-performance indexing CLI."""
    pass

@cli.command()
@click.option('--uri', required=True, help="MongoDB Connection URI")
@click.option('--db', required=True, help="Database Name")
@click.option('--coll', required=True, help="Collection Name")
@click.option('--field', required=True, help="Field to index (e.g., bot_name)")
def sync(uri, db, coll, field):
    """Start the full synchronization from Mongo to Local Index."""
    
    # 1. Setup the Adapter
    config = {
        "uri": uri,
        "db": db,
        "collection": coll,
        "search_field": field,
        "metadata_fields": ["owner_id", "org_id"] # Add any others you need
    }
    adapter = MongoAdapter(config)

    # 2. Setup the Engine
    # Store the index in a folder named after the collection
    index_path = f".quicksearch_index/{adapter.get_identifier()}"
    engine = SearchEngine(index_path=index_path, filterable_fields=config["metadata_fields"])

    async def run_sync():
        click.echo(f"🚀 Starting sync for {db}.{coll}...")
        # In a real scenario, you'd fetch the last_id from a checkpoint file
        # For now, we start from the beginning
        record_stream = adapter.stream_records(last_id=None)
        await engine.index_records(record_stream)
        click.echo("✅ Sync completed successfully!")

    asyncio.run(run_sync())

if __name__ == "__main__":
    cli()