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
    
    activity.logger.info(f"[BATCH START] Fetching from {platform}, batch_size={batch_size}")
    
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        
        # Callback to track batch progress
        batch_count = 0
        def log_progress(stats):
            nonlocal batch_count
            batch_count += 1
            activity.logger.info(
                f"[BATCH {batch_count}] Indexed {stats.total_indexed} products "
                f"(fetched: {stats.total_fetched}, failed: {stats.total_failed})"
            )
            activity.heartbeat(f"Batch {batch_count}: {stats.total_indexed} products")
        
        # Index from platform with progress callback
        stats = await service.index_from_platform(
            platform=platform,
            batch_size=batch_size,
            on_progress=log_progress,
        )
        
        activity.logger.info(
            f"[BATCH COMPLETE] Total indexed: {stats.total_indexed} products "
            f"in {batch_count} batches ({stats.duration_seconds:.1f}s)"
        )
        
        return {
            "status": "success",
            "platform": platform,
            "indexed": stats.total_indexed,
            "batches": batch_count,
            "duration_seconds": stats.duration_seconds,
            "errors": [],
        }
    
    except Exception as e:
        activity.logger.error(f"[BATCH ERROR] Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "platform": platform,
            "indexed": 0,
            "batches": 0,
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
    """
    Send trace to Langfuse for observability.
    
    TODO: Implement proper Langfuse SDK integration in Phase 1.3
    For now, just log and skip to avoid blocking workflows.
    """
    activity.logger.debug(f"Langfuse trace (skipped): {trace_data.get('name')}")
    return True  # Return success to not block workflow
