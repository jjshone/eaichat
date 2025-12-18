"""
Indexing API Router
===================

Endpoints for product indexing and search.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import os

router = APIRouter(prefix="/api/index", tags=["indexing"])


class PlatformEnum(str, Enum):
    fakestore = "fakestore"
    magento = "magento"
    odoo = "odoo"


class IndexRequest(BaseModel):
    platform: PlatformEnum = PlatformEnum.fakestore
    batch_size: int = Field(default=50, ge=1, le=500)
    include_images: bool = False


class IndexResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    category: Optional[str] = None
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    platform: Optional[str] = None
    hybrid: bool = False
    alpha: float = Field(default=0.5, ge=0, le=1)


class SearchResult(BaseModel):
    id: str
    score: float
    title: str
    description: str
    price: float
    category: str
    image_url: str
    platform: str


@router.post("/sync", response_model=IndexResponse)
async def sync_products(request: IndexRequest):
    """
    Sync products from a platform to vector database using Temporal workflow.
    
    This triggers a durable workflow that handles batching, retries, and progress tracking.
    """
    try:
        from temporalio.client import Client
        import uuid
        
        # Connect to Temporal
        temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
        temporal_port = int(os.getenv("TEMPORAL_PORT", "7233"))
        client = await Client.connect(f"{temporal_host}:{temporal_port}")
        
        # Generate workflow ID
        workflow_id = f"product-sync-{request.platform.value}-{uuid.uuid4().hex[:8]}"
        
        # Start workflow
        handle = await client.start_workflow(
            "ProductSyncWorkflow",
            args=[request.platform.value, request.batch_size],
            id=workflow_id,
            task_queue="eaichat-tasks",
        )
        
        return IndexResponse(
            status="started",
            message=f"Indexing from {request.platform.value} started via Temporal",
            job_id=workflow_id,
        )
    except Exception as e:
        # Fallback to background task if Temporal unavailable
        print(f"[WARN] Temporal unavailable, using background task: {e}")
        from app.services.indexing_service import get_indexing_service
        from fastapi import BackgroundTasks
        
        service = get_indexing_service()
        
        async def run_indexing():
            try:
                await service.index_from_platform(
                    platform=request.platform.value,
                    batch_size=request.batch_size,
                )
            except Exception as err:
                print(f"[ERROR] Indexing failed: {err}")
        
        # Note: Can't use BackgroundTasks without it being injected
        # Execute directly for now
        import asyncio
        asyncio.create_task(run_indexing())
        
        return IndexResponse(
            status="started",
            message=f"Indexing from {request.platform.value} started (fallback mode)"
        )


@router.post("/search", response_model=list[SearchResult])
async def search_products(request: SearchRequest):
    """
    Search products using vector similarity.
    
    Supports:
    - Semantic search with query embedding
    - Hybrid search (vector + keyword)
    - Filtering by category, price, platform
    """
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        
        if request.hybrid:
            results = await service.hybrid_search_products(
                query=request.query,
                limit=request.limit,
                alpha=request.alpha,
            )
        else:
            results = await service.search_products(
                query=request.query,
                limit=request.limit,
                category=request.category,
                min_price=request.min_price,
                max_price=request.max_price,
                platform=request.platform,
            )
        
        return [
            SearchResult(
                id=str(r.get("id", "")),
                score=r.get("score", 0),
                title=r.get("title", ""),
                description=r.get("description", "")[:200],
                price=r.get("price", 0),
                category=r.get("category", ""),
                image_url=r.get("image_url", ""),
                platform=r.get("platform", ""),
            )
            for r in results
        ]
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get statistics about the products collection."""
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        stats = await service.get_collection_stats()
        
        return {
            "status": "ok",
            **stats
        }
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/create-collection")
async def create_collection(recreate: bool = False):
    """Create or recreate the products collection."""
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        success = await service.ensure_collection(recreate=recreate)
        
        if success:
            return {"status": "ok", "message": "Collection ready"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create collection")
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")


@router.delete("/platform/{platform}")
async def delete_platform_products(platform: PlatformEnum):
    """Delete all products from a specific platform."""
    try:
        from app.services.indexing_service import get_indexing_service
        
        service = get_indexing_service()
        await service.delete_by_platform(platform.value)
        
        return {"status": "ok", "message": f"Deleted products from {platform.value}"}
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
