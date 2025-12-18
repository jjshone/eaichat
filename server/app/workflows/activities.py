"""
Temporal Activities for eaichat workflows
=========================================

Activities are the actual work units executed by Temporal workers.
"""

from temporalio import activity

# Import from product indexer
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.product_indexer import (
    fetch_and_index_from_fake_store,
    get_products_from_mysql,
    upsert_product_vectors,
    get_reindex_checkpoint as _get_checkpoint,
    update_reindex_checkpoint as _update_checkpoint,
)


@activity.defn
async def fetch_and_index_products(source: str) -> int:
    """Activity to fetch products from external source and index them."""
    activity.logger.info(f"Fetching products from {source}")
    
    if source == "fakestore":
        success = fetch_and_index_from_fake_store()
        return 1 if success else 0
    
    return 0


@activity.defn
async def reindex_products_batch(params: dict) -> dict:
    """Activity to reindex a batch of products."""
    batch_size = params.get("batch_size", 32)
    offset = params.get("offset", 0)
    
    activity.logger.info(f"Reindexing batch: offset={offset}, size={batch_size}")
    
    products = get_products_from_mysql(limit=batch_size, offset=offset)
    if not products:
        return {"count": 0, "last_id": offset}
    
    indexed = upsert_product_vectors(products)
    last_id = max(p.id for p in products) if products else offset
    
    return {"count": indexed, "last_id": last_id}


@activity.defn
async def get_reindex_checkpoint(collection: str) -> int:
    """Activity to get current reindex checkpoint."""
    return _get_checkpoint(collection)


@activity.defn
async def update_reindex_checkpoint(params: dict) -> bool:
    """Activity to update reindex checkpoint."""
    collection = params.get("collection", "products")
    last_id = params.get("last_id", 0)
    _update_checkpoint(collection, last_id)
    return True


@activity.defn
async def send_langfuse_event(event_data: dict) -> bool:
    """Activity to send telemetry event to Langfuse."""
    try:
        from langfuse import Langfuse
        
        langfuse = Langfuse()
        langfuse.trace(
            name=event_data.get("event", "unknown"),
            metadata=event_data,
        )
        return True
    except Exception as e:
        activity.logger.warning(f"Failed to send Langfuse event: {e}")
        return False
