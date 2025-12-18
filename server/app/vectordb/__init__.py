"""
Vector Database Abstraction Layer
=================================

Provides a unified interface for vector databases (Qdrant, Typesense).
Allows switching between backends via configuration.

Usage:
    from app.vectordb import get_vector_client
    
    client = get_vector_client()  # Returns configured backend
    await client.create_collection("products", schema)
    await client.upsert(collection, points)
    results = await client.search(collection, query_vector)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import os


class VectorDBBackend(Enum):
    QDRANT = "qdrant"
    TYPESENSE = "typesense"


@dataclass
class VectorPoint:
    """A single vector point with ID, vector(s), and payload."""
    id: str | int
    vectors: dict[str, list[float]]  # Named vectors: {"text": [...], "image": [...]}
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result with score and payload."""
    id: str | int
    score: float
    payload: dict[str, Any]


@dataclass
class CollectionSchema:
    """Schema definition for a collection."""
    name: str
    vectors: dict[str, dict]  # {"text": {"size": 384, "distance": "cosine"}}
    payload_indexes: list[str] = field(default_factory=list)


class BaseVectorClient(ABC):
    """Abstract base class for vector database clients."""
    
    @abstractmethod
    async def create_collection(self, schema: CollectionSchema) -> bool:
        """Create a collection with the given schema."""
        pass
    
    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        pass
    
    @abstractmethod
    async def get_collection_info(self, name: str) -> dict:
        """Get collection statistics and info."""
        pass
    
    @abstractmethod
    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        """Upsert points to collection. Returns count of upserted points."""
        pass
    
    @abstractmethod
    async def delete(self, collection: str, ids: list[str | int]) -> bool:
        """Delete points by IDs."""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        vector_name: str = "text",
        limit: int = 10,
        filters: Optional[dict] = None,
        with_payload: bool = True,
    ) -> list[SearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    async def hybrid_search(
        self,
        collection: str,
        vector: list[float],
        query_text: str,
        vector_name: str = "text",
        limit: int = 10,
        alpha: float = 0.5,  # Balance between vector and text search
    ) -> list[SearchResult]:
        """Hybrid search combining vector similarity and keyword matching."""
        pass
    
    @abstractmethod
    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> tuple[list[SearchResult], Optional[str]]:
        """Scroll through all points. Returns (points, next_offset)."""
        pass
    
    @abstractmethod
    async def count(self, collection: str) -> int:
        """Count points in collection."""
        pass


def get_vector_backend() -> VectorDBBackend:
    """Get configured vector database backend."""
    backend = os.getenv("VECTOR_DB_BACKEND", "qdrant").lower()
    return VectorDBBackend(backend)


def get_vector_client() -> BaseVectorClient:
    """Get configured vector database client."""
    backend = get_vector_backend()
    
    if backend == VectorDBBackend.QDRANT:
        from .qdrant_client import QdrantVectorClient
        return QdrantVectorClient()
    elif backend == VectorDBBackend.TYPESENSE:
        from .typesense_client import TypesenseVectorClient
        return TypesenseVectorClient()
    else:
        raise ValueError(f"Unknown vector backend: {backend}")
