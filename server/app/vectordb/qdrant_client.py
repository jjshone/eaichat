"""
Qdrant Vector Client Implementation
====================================

Implements the BaseVectorClient interface for Qdrant.
"""

import os
from typing import Optional
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    NamedVector,
)

from . import BaseVectorClient, VectorPoint, SearchResult, CollectionSchema


class QdrantVectorClient(BaseVectorClient):
    """Qdrant implementation of vector database client."""
    
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.url = f"http://{self.host}:{self.port}"
        
        # Sync client for simple operations
        self._sync_client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            prefer_grpc=False,
        )
        
        # Async client for async operations
        self._async_client: Optional[AsyncQdrantClient] = None
    
    async def _get_async_client(self) -> AsyncQdrantClient:
        if self._async_client is None:
            self._async_client = AsyncQdrantClient(
                url=self.url,
                api_key=self.api_key,
                prefer_grpc=False,
            )
        return self._async_client
    
    def _distance_to_qdrant(self, distance: str) -> Distance:
        mapping = {
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID,
            "dot": Distance.DOT,
            "manhattan": Distance.MANHATTAN,
        }
        return mapping.get(distance.lower(), Distance.COSINE)
    
    async def create_collection(self, schema: CollectionSchema) -> bool:
        """Create a Qdrant collection with named vectors."""
        client = await self._get_async_client()
        
        # Build vectors config for named vectors
        vectors_config = {}
        for name, config in schema.vectors.items():
            vectors_config[name] = VectorParams(
                size=config["size"],
                distance=self._distance_to_qdrant(config.get("distance", "cosine")),
            )
        
        try:
            await client.create_collection(
                collection_name=schema.name,
                vectors_config=vectors_config,
            )
            
            # Create payload indexes for efficient filtering
            for field in schema.payload_indexes:
                await client.create_payload_index(
                    collection_name=schema.name,
                    field_name=field,
                    field_schema="keyword",  # Default to keyword index
                )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create collection {schema.name}: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        client = await self._get_async_client()
        try:
            await client.delete_collection(collection_name=name)
            return True
        except Exception:
            return False
    
    async def collection_exists(self, name: str) -> bool:
        client = await self._get_async_client()
        try:
            collections = await client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception:
            return False
    
    async def get_collection_info(self, name: str) -> dict:
        client = await self._get_async_client()
        try:
            info = await client.get_collection(collection_name=name)
            return {
                "name": name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
                "config": {
                    "vectors": {
                        k: {"size": v.size, "distance": v.distance.value}
                        for k, v in (info.config.params.vectors or {}).items()
                    }
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        client = await self._get_async_client()
        
        qdrant_points = []
        for p in points:
            qdrant_points.append(PointStruct(
                id=p.id if isinstance(p.id, int) else hash(p.id) % (2**63),
                vector=p.vectors,  # Qdrant supports named vectors dict directly
                payload=p.payload,
            ))
        
        try:
            await client.upsert(
                collection_name=collection,
                points=qdrant_points,
            )
            return len(qdrant_points)
        except Exception as e:
            print(f"[ERROR] Failed to upsert to {collection}: {e}")
            return 0
    
    async def delete(self, collection: str, ids: list[str | int]) -> bool:
        client = await self._get_async_client()
        try:
            # Convert string IDs to hashes if needed
            point_ids = [
                i if isinstance(i, int) else hash(i) % (2**63)
                for i in ids
            ]
            await client.delete(
                collection_name=collection,
                points_selector=point_ids,
            )
            return True
        except Exception:
            return False
    
    def _build_filter(self, filters: dict) -> Optional[Filter]:
        """Build Qdrant filter from dict."""
        if not filters:
            return None
        
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                # Range filter: {"price": {"gte": 10, "lte": 100}}
                conditions.append(FieldCondition(
                    key=key,
                    range=Range(**value),
                ))
            else:
                # Exact match
                conditions.append(FieldCondition(
                    key=key,
                    match=MatchValue(value=value),
                ))
        
        return Filter(must=conditions) if conditions else None
    
    async def search(
        self,
        collection: str,
        vector: list[float],
        vector_name: str = "text",
        limit: int = 10,
        filters: Optional[dict] = None,
        with_payload: bool = True,
    ) -> list[SearchResult]:
        client = await self._get_async_client()
        
        try:
            results = await client.query_points(
                collection_name=collection,
                query=vector,
                using=vector_name,
                limit=limit,
                query_filter=self._build_filter(filters),
                with_payload=with_payload,
            )
            
            return [
                SearchResult(
                    id=r.id,
                    score=r.score,
                    payload=r.payload or {},
                )
                for r in results.points
            ]
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []
    
    async def hybrid_search(
        self,
        collection: str,
        vector: list[float],
        query_text: str,
        vector_name: str = "text",
        limit: int = 10,
        alpha: float = 0.5,
    ) -> list[SearchResult]:
        """
        Hybrid search combining dense vector and sparse text matching.
        Note: Requires Qdrant 1.10+ with Query API for true hybrid search.
        This implementation uses dense search with text filtering.
        """
        client = await self._get_async_client()
        
        try:
            # For true hybrid search, use Qdrant Query API (v1.10+)
            # This is a simplified version using payload text search
            results = await client.query_points(
                collection_name=collection,
                query=vector,
                using=vector_name,
                limit=limit * 2,  # Get more results for reranking
                with_payload=True,
            )
            
            # Simple text boost: increase score if query terms appear in payload
            query_terms = set(query_text.lower().split())
            boosted_results = []
            
            for r in results.points:
                payload_text = " ".join(
                    str(v).lower() for v in (r.payload or {}).values()
                    if isinstance(v, str)
                )
                
                # Count matching terms
                matches = sum(1 for term in query_terms if term in payload_text)
                text_score = matches / max(len(query_terms), 1)
                
                # Blend scores
                hybrid_score = (1 - alpha) * r.score + alpha * text_score
                boosted_results.append((hybrid_score, r))
            
            # Sort by hybrid score and take top results
            boosted_results.sort(key=lambda x: x[0], reverse=True)
            
            return [
                SearchResult(
                    id=r.id,
                    score=score,
                    payload=r.payload or {},
                )
                for score, r in boosted_results[:limit]
            ]
        except Exception as e:
            print(f"[ERROR] Hybrid search failed: {e}")
            return []
    
    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> tuple[list[SearchResult], Optional[str]]:
        client = await self._get_async_client()
        
        try:
            results, next_offset = await client.scroll(
                collection_name=collection,
                limit=limit,
                offset=int(offset) if offset else None,
                with_payload=True,
                query_filter=self._build_filter(filters),
            )
            
            points = [
                SearchResult(
                    id=r.id,
                    score=1.0,  # No score in scroll
                    payload=r.payload or {},
                )
                for r in results
            ]
            
            return points, str(next_offset) if next_offset else None
        except Exception as e:
            print(f"[ERROR] Scroll failed: {e}")
            return [], None
    
    async def count(self, collection: str) -> int:
        client = await self._get_async_client()
        try:
            info = await client.get_collection(collection_name=collection)
            return info.points_count or 0
        except Exception:
            return 0
