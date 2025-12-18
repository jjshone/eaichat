"""
Typesense Vector Client Implementation
======================================

Implements the BaseVectorClient interface for Typesense.
Typesense supports vector search starting from v0.25.0.
"""

import os
from typing import Optional
import typesense

from . import BaseVectorClient, VectorPoint, SearchResult, CollectionSchema


class TypesenseVectorClient(BaseVectorClient):
    """Typesense implementation of vector database client."""
    
    def __init__(self):
        self.host = os.getenv("TYPESENSE_HOST", "localhost")
        self.port = os.getenv("TYPESENSE_PORT", "8108")
        self.protocol = os.getenv("TYPESENSE_PROTOCOL", "http")
        self.api_key = os.getenv("TYPESENSE_API_KEY", "xyz")
        
        self._client = typesense.Client({
            "nodes": [{
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
            }],
            "api_key": self.api_key,
            "connection_timeout_seconds": 10,
        })
    
    def _schema_to_typesense(self, schema: CollectionSchema) -> dict:
        """Convert our schema format to Typesense schema."""
        fields = []
        
        # Add vector fields
        for name, config in schema.vectors.items():
            fields.append({
                "name": name,
                "type": f"float[]",
                "num_dim": config["size"],
                "embed": {
                    "from": [],  # Will be provided at index time
                    "model_config": {"model_name": "manual"},
                }
            })
        
        # Add common payload fields
        common_fields = [
            {"name": "product_id", "type": "string", "facet": True},
            {"name": "title", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "price", "type": "float", "facet": True},
            {"name": "category", "type": "string", "facet": True},
            {"name": "image_url", "type": "string"},
            {"name": "platform", "type": "string", "facet": True},
            {"name": "in_stock", "type": "bool", "facet": True},
        ]
        fields.extend(common_fields)
        
        return {
            "name": schema.name,
            "fields": fields,
        }
    
    async def create_collection(self, schema: CollectionSchema) -> bool:
        try:
            ts_schema = self._schema_to_typesense(schema)
            self._client.collections.create(ts_schema)
            return True
        except typesense.exceptions.ObjectAlreadyExists:
            return True  # Collection already exists
        except Exception as e:
            print(f"[ERROR] Failed to create Typesense collection: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        try:
            self._client.collections[name].delete()
            return True
        except Exception:
            return False
    
    async def collection_exists(self, name: str) -> bool:
        try:
            self._client.collections[name].retrieve()
            return True
        except typesense.exceptions.ObjectNotFound:
            return False
        except Exception:
            return False
    
    async def get_collection_info(self, name: str) -> dict:
        try:
            info = self._client.collections[name].retrieve()
            return {
                "name": info["name"],
                "num_documents": info.get("num_documents", 0),
                "fields": info.get("fields", []),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        documents = []
        for p in points:
            doc = {
                "id": str(p.id),
                **p.vectors,  # Include vector fields
                **p.payload,  # Include payload fields
            }
            documents.append(doc)
        
        try:
            result = self._client.collections[collection].documents.import_(
                documents,
                {"action": "upsert"},
            )
            # Count successful imports
            success_count = sum(1 for r in result if r.get("success", False))
            return success_count
        except Exception as e:
            print(f"[ERROR] Typesense upsert failed: {e}")
            return 0
    
    async def delete(self, collection: str, ids: list[str | int]) -> bool:
        try:
            for id_ in ids:
                self._client.collections[collection].documents[str(id_)].delete()
            return True
        except Exception:
            return False
    
    async def search(
        self,
        collection: str,
        vector: list[float],
        vector_name: str = "text",
        limit: int = 10,
        filters: Optional[dict] = None,
        with_payload: bool = True,
    ) -> list[SearchResult]:
        try:
            # Build filter string
            filter_by = ""
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # Range filter
                        if "gte" in value:
                            filter_parts.append(f"{key}:>={value['gte']}")
                        if "lte" in value:
                            filter_parts.append(f"{key}:<={value['lte']}")
                    else:
                        filter_parts.append(f"{key}:={value}")
                filter_by = " && ".join(filter_parts)
            
            search_params = {
                "q": "*",
                "vector_query": f"{vector_name}:({','.join(map(str, vector))})",
                "per_page": limit,
            }
            
            if filter_by:
                search_params["filter_by"] = filter_by
            
            results = self._client.collections[collection].documents.search(search_params)
            
            return [
                SearchResult(
                    id=hit["document"]["id"],
                    score=hit.get("vector_distance", 0),
                    payload=hit["document"],
                )
                for hit in results.get("hits", [])
            ]
        except Exception as e:
            print(f"[ERROR] Typesense search failed: {e}")
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
        """Typesense hybrid search using both vector and text queries."""
        try:
            search_params = {
                "q": query_text,
                "query_by": "title,description",
                "vector_query": f"{vector_name}:({','.join(map(str, vector))})",
                "per_page": limit,
            }
            
            results = self._client.collections[collection].documents.search(search_params)
            
            return [
                SearchResult(
                    id=hit["document"]["id"],
                    score=hit.get("hybrid_search_info", {}).get("rank_fusion_score", 0),
                    payload=hit["document"],
                )
                for hit in results.get("hits", [])
            ]
        except Exception as e:
            print(f"[ERROR] Typesense hybrid search failed: {e}")
            return []
    
    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> tuple[list[SearchResult], Optional[str]]:
        try:
            page = int(offset) if offset else 1
            
            search_params = {
                "q": "*",
                "per_page": limit,
                "page": page,
            }
            
            results = self._client.collections[collection].documents.search(search_params)
            
            points = [
                SearchResult(
                    id=hit["document"]["id"],
                    score=1.0,
                    payload=hit["document"],
                )
                for hit in results.get("hits", [])
            ]
            
            # Check if there are more pages
            total = results.get("found", 0)
            next_offset = str(page + 1) if (page * limit) < total else None
            
            return points, next_offset
        except Exception as e:
            print(f"[ERROR] Typesense scroll failed: {e}")
            return [], None
    
    async def count(self, collection: str) -> int:
        try:
            info = self._client.collections[collection].retrieve()
            return info.get("num_documents", 0)
        except Exception:
            return 0
