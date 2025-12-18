"""
Indexing Service
================

Orchestrates the product indexing pipeline:
Connector → Embeddings → Vector DB

Supports:
- Multiple platform connectors
- Batch processing
- Temporal workflow integration
- Progress tracking
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from app.connectors import get_connector, ProductData, ConnectorConfig
from app.services.embedding_service import EmbeddingService
from app.vectordb import (
    get_vector_client,
    VectorPoint,
    CollectionSchema,
)


@dataclass
class IndexingStats:
    """Statistics from an indexing run."""
    total_fetched: int = 0
    total_indexed: int = 0
    total_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0


class IndexingService:
    """
    Service for indexing products from platforms to vector database.
    
    This is the main orchestration layer that:
    1. Fetches products from a platform connector
    2. Generates embeddings (text and optionally image)
    3. Upserts to vector database (Qdrant or Typesense)
    """
    
    COLLECTION_NAME = "products"
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_client = get_vector_client()
    
    async def ensure_collection(self, recreate: bool = False) -> bool:
        """Ensure the products collection exists with proper schema."""
        exists = await self.vector_client.collection_exists(self.COLLECTION_NAME)
        
        if exists and recreate:
            await self.vector_client.delete_collection(self.COLLECTION_NAME)
            exists = False
        
        if not exists:
            schema = CollectionSchema(
                name=self.COLLECTION_NAME,
                vectors={
                    "text": {
                        "size": self.embedding_service.text_embedding_size,
                        "distance": "cosine",
                    },
                    # Image vectors are optional - added if model is loaded
                    # "image": {
                    #     "size": self.embedding_service.image_embedding_size,
                    #     "distance": "cosine",
                    # },
                },
                payload_indexes=[
                    "category",
                    "platform",
                    "price",
                    "in_stock",
                ],
            )
            return await self.vector_client.create_collection(schema)
        
        return True
    
    async def index_from_platform(
        self,
        platform: str,
        config: Optional[ConnectorConfig] = None,
        batch_size: int = 50,
        include_images: bool = False,
        on_progress: Optional[callable] = None,
    ) -> IndexingStats:
        """
        Index all products from a platform.
        
        Args:
            platform: Platform name (fakestore, magento, odoo)
            config: Optional connector configuration
            batch_size: Number of products to process per batch
            include_images: Whether to generate image embeddings
            on_progress: Optional callback(stats) called after each batch
        
        Returns:
            IndexingStats with totals
        """
        stats = IndexingStats(started_at=datetime.now())
        
        # Ensure collection exists
        await self.ensure_collection()
        
        # Get connector
        connector = get_connector(platform, config)
        
        try:
            # Fetch and index in batches
            async for products in connector.fetch_products(batch_size=batch_size):
                stats.total_fetched += len(products)
                
                # Generate embeddings and create vector points
                points = await self._create_vector_points(
                    products,
                    include_images=include_images,
                )
                
                # Upsert to vector DB
                indexed = await self.vector_client.upsert(
                    self.COLLECTION_NAME,
                    points,
                )
                
                stats.total_indexed += indexed
                stats.total_failed += len(products) - indexed
                
                if on_progress:
                    on_progress(stats)
                
                # Yield control for async tasks
                await asyncio.sleep(0.01)
        
        except Exception as e:
            print(f"[ERROR] Indexing failed: {e}")
            raise
        finally:
            stats.completed_at = datetime.now()
        
        return stats
    
    async def _create_vector_points(
        self,
        products: list[ProductData],
        include_images: bool = False,
    ) -> list[VectorPoint]:
        """Create vector points from products."""
        points = []
        
        # Batch embed texts for efficiency
        texts = [
            f"{p.title}. {p.description}. Category: {p.category}"
            for p in products
        ]
        text_embeddings = self.embedding_service.embed_texts(texts)
        
        for i, product in enumerate(products):
            vectors = {"text": text_embeddings[i]}
            
            # Optional image embedding
            if include_images and product.image_url:
                img_embedding = self.embedding_service.embed_image_from_url(
                    product.image_url
                )
                if img_embedding:
                    vectors["image"] = img_embedding
            
            point = VectorPoint(
                id=product.external_id,
                vectors=vectors,
                payload={
                    "product_id": product.external_id,
                    "title": product.title,
                    "description": product.description[:500],  # Truncate for storage
                    "price": product.price,
                    "category": product.category,
                    "image_url": product.image_url,
                    "platform": product.platform,
                    "rating": product.rating,
                    "in_stock": product.in_stock,
                },
            )
            points.append(point)
        
        return points
    
    async def search_products(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        platform: Optional[str] = None,
    ) -> list[dict]:
        """
        Search products using vector similarity.
        
        Returns list of products with scores.
        """
        # Generate query embedding
        query_vector = self.embedding_service.embed_text(query)
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if platform:
            filters["platform"] = platform
        if min_price is not None or max_price is not None:
            filters["price"] = {}
            if min_price is not None:
                filters["price"]["gte"] = min_price
            if max_price is not None:
                filters["price"]["lte"] = max_price
        
        # Search
        results = await self.vector_client.search(
            collection=self.COLLECTION_NAME,
            vector=query_vector,
            vector_name="text",
            limit=limit,
            filters=filters if filters else None,
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                **r.payload,
            }
            for r in results
        ]
    
    async def hybrid_search_products(
        self,
        query: str,
        limit: int = 10,
        alpha: float = 0.5,
    ) -> list[dict]:
        """
        Hybrid search combining vector similarity and keyword matching.
        """
        query_vector = self.embedding_service.embed_text(query)
        
        results = await self.vector_client.hybrid_search(
            collection=self.COLLECTION_NAME,
            vector=query_vector,
            query_text=query,
            limit=limit,
            alpha=alpha,
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                **r.payload,
            }
            for r in results
        ]
    
    async def get_collection_stats(self) -> dict:
        """Get statistics about the products collection."""
        info = await self.vector_client.get_collection_info(self.COLLECTION_NAME)
        return info
    
    async def delete_by_platform(self, platform: str) -> bool:
        """Delete all products from a specific platform."""
        # Qdrant doesn't support batch delete by filter in the simple API
        # We need to scroll and delete in batches
        deleted_count = 0
        offset = None
        
        while True:
            results, offset = await self.vector_client.scroll(
                collection=self.COLLECTION_NAME,
                limit=100,
                offset=offset,
                filters={"platform": platform},
            )
            
            if not results:
                break
            
            ids = [r.id for r in results]
            await self.vector_client.delete(self.COLLECTION_NAME, ids)
            deleted_count += len(ids)
            
            if offset is None:
                break
        
        print(f"[INFO] Deleted {deleted_count} products from platform: {platform}")
        return True


# Convenience function
def get_indexing_service() -> IndexingService:
    """Get indexing service instance."""
    return IndexingService()
