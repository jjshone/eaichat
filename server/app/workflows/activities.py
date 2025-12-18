"""
Temporal Activities using New Architecture
==========================================

Activities for product indexing using IndexingService and platform connectors.
"""

from temporalio import activity
from typing import Optional
import asyncio


@activity.defn
async def fetch_and_index_from_platform(params: dict) -> dict:
    """
    Fetch products from platform connector and index to vector DB.
    
    Args:
        params: Dict with 'platform' and 'batch_size'
        
    Returns:
        dict with status, indexed count, errors
    """
    platform = params.get("platform", "fakestore")
    batch_size = params.get("batch_size", 50)
    
    activity.logger.info(f"Fetching and indexing from {platform}, batch_size={batch_size}")
    
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        
        # Send heartbeat periodically
        activity.heartbeat(f"Starting sync from {platform}")
        
        # Index from platform (note: IndexingService doesn't have progress_callback)
        stats = await service.index_from_platform(
            platform=platform,
            batch_size=batch_size,
        )
        
        activity.logger.info(f"Indexed {stats.total_indexed} products from {platform}")
        
        return {
            "status": "success",
            "platform": platform,
            "indexed": stats.total_indexed,
            "errors": [],
        }
    
    except Exception as e:
        activity.logger.error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Check if Langfuse is configured
        if not os.getenv("LANGFUSE_PUBLIC_KEY") and not os.getenv("LANGFUSE_SECRET_KEY"):
            activity.logger.debug("Langfuse not configured, skipping trace")
            return False
        
        from langfuse import Langfuse
        
        langfuse = Langfuse()
        
        # langfuse-3.x uses generation/span API, not trace()
        # Create a simple event for now
        langfuse.generation(
            name=trace_data.get("name", "temporal_activity"),
            metadata=trace_data.get("metadata", {}),
            tags=trace_data.get("tags", []),
        )
        langfuse.flush()
        
        return True
    except Exception as e:
        activity.logger.warning(f"Langfuse trace failed: {e}")
        return False
