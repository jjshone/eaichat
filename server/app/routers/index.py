"""
API Endpoints for Product Indexing
==================================

Provides REST endpoints for triggering product indexing operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(prefix="/api/index", tags=["indexing"])


class IndexResponse(BaseModel):
    status: str
    message: str
    count: Optional[int] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class SearchResult(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str
    score: float


@router.post("/fetch-products", response_model=IndexResponse)
async def fetch_and_index_products(background_tasks: BackgroundTasks):
    """Fetch products from Fake Store API and index to Qdrant."""
    try:
        from scripts.product_indexer import fetch_and_index_from_fake_store
        
        # Run in background
        background_tasks.add_task(fetch_and_index_from_fake_store)
        
        return IndexResponse(
            status="queued",
            message="Product fetch and index task started in background"
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Indexing dependencies not available: {e}"
        )


@router.post("/reindex", response_model=IndexResponse)
async def trigger_reindex(background_tasks: BackgroundTasks, batch_size: int = 32):
    """Trigger full product reindex from MySQL to Qdrant."""
    try:
        from scripts.product_indexer import reindex_all_products
        
        background_tasks.add_task(reindex_all_products, batch_size=batch_size, resume=True)
        
        return IndexResponse(
            status="queued",
            message=f"Reindex task started in background (batch_size={batch_size})"
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Indexing dependencies not available: {e}"
        )


@router.post("/search", response_model=list[SearchResult])
async def search_products(request: SearchRequest):
    """Search products using vector similarity."""
    try:
        from scripts.product_indexer import search_similar_products
        
        results = search_similar_products(
            query=request.query,
            top_k=request.top_k,
            category_filter=request.category,
            min_price=request.min_price,
            max_price=request.max_price,
        )
        
        return [
            SearchResult(
                id=r.get("id", 0),
                title=r.get("title", ""),
                description=r.get("description", "")[:200],
                price=r.get("price", 0.0),
                category=r.get("category", ""),
                score=r.get("score", 0.0),
            )
            for r in results
        ]
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Search dependencies not available: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {e}"
        )


@router.get("/stats")
async def get_index_stats():
    """Get Qdrant collection statistics."""
    try:
        from scripts.product_indexer import get_collection_stats
        
        stats = get_collection_stats()
        if not stats:
            return {"status": "no_collection", "message": "Products collection not found"}
        
        return {
            "status": "ok",
            **stats
        }
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Stats dependencies not available: {e}"
        )


@router.post("/create-schema")
async def create_collection_schema(recreate: bool = False):
    """Create or recreate Qdrant collection schema."""
    try:
        from scripts.product_indexer import create_collection_schema
        
        success = create_collection_schema(recreate=recreate)
        
        if success:
            return IndexResponse(
                status="ok",
                message="Collection schema created successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create collection schema")
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Schema dependencies not available: {e}"
        )
