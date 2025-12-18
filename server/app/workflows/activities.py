"""
Temporal Activities using New Architecture
==========================================

Activities for product indexing using IndexingService and platform connectors.
"""

from temporalio import activity
from typing import Optional
import asyncio


@activity.defn
async def fetch_and_index_from_platform(platform: str, batch_size: int = 50) -> dict:
    """
    Fetch products from platform connector and index to vector DB.
    
    Args:
        platform: Platform name (fakestore, magento, odoo)
        batch_size: Batch size for indexing
        
    Returns:
        dict with status, indexed count, errors
    """
    activity.logger.info(f"Fetching and indexing from {platform}")
    
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        
        total_indexed = 0
        errors = []
        
        def progress_callback(current: int, total: int):
            activity.logger.info(f"Progress: {current}/{total}")
            activity.heartbeat(f"{current}/{total}")
        
        total_indexed = await service.index_from_platform(
            platform=platform,
            batch_size=batch_size,
            progress_callback=progress_callback,
        )
        
        return {
            "status": "success",
            "platform": platform,
            "indexed": total_indexed,
            "errors": errors,
        }
    
    except Exception as e:
        activity.logger.error(f"Indexing failed: {e}")
        return {
            "status": "error",
            "platform": platform,
            "indexed": 0,
            "errors": [str(e)],
        }


@activity.defn
async def ensure_vector_collection() -> dict:
    """Ensure vector collection exists with proper schema."""
    activity.logger.info("Ensuring vector collection exists")
    
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        await service.ensure_collection()
        
        return {"status": "success", "collection": "products"}
    except Exception as e:
        activity.logger.error(f"Collection check failed: {e}")
        return {"status": "error", "error": str(e)}


@activity.defn
async def get_collection_stats() -> dict:
    """Get vector collection statistics."""
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        stats = await service.get_collection_stats()
        
        return {"status": "success", "stats": stats}
    except Exception as e:
        activity.logger.error(f"Stats retrieval failed: {e}")
        return {"status": "error", "error": str(e)}


@activity.defn
async def delete_platform_products(platform: str) -> dict:
    """Delete all products for a specific platform."""
    activity.logger.info(f"Deleting products from {platform}")
    
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        deleted = await service.delete_by_platform(platform)
        
        return {"status": "success", "platform": platform, "deleted": deleted}
    except Exception as e:
        activity.logger.error(f"Deletion failed: {e}")
        return {"status": "error", "platform": platform, "error": str(e)}


@activity.defn
async def send_langfuse_trace(trace_data: dict) -> bool:
    """Send trace to Langfuse for observability."""
    try:
        import os
        from langfuse import Langfuse
        
        # Check if Langfuse is configured
        if not os.getenv("LANGFUSE_PUBLIC_KEY"):
            activity.logger.debug("Langfuse not configured, skipping trace")
            return False
        
        langfuse = Langfuse()
        langfuse.trace(
            name=trace_data.get("name", "temporal_activity"),
            metadata=trace_data.get("metadata", {}),
            tags=trace_data.get("tags", []),
        )
        langfuse.flush()
        
        return True
    except Exception as e:
        activity.logger.warning(f"Langfuse trace failed: {e}")
        return False
