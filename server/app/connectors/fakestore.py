"""
Fake Store API Connector
========================

Fetches products from https://fakestoreapi.com
Used for demonstration and testing purposes.
"""

import httpx
from typing import AsyncIterator, Optional

from . import BasePlatformConnector, ProductData, ConnectorConfig, PlatformType


class FakeStoreConnector(BasePlatformConnector):
    """Connector for Fake Store API (fakestoreapi.com)."""
    
    def __init__(self, config: Optional[ConnectorConfig] = None):
        if config is None:
            config = ConnectorConfig(
                platform=PlatformType.FAKESTORE,
                base_url="https://fakestoreapi.com",
            )
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=30.0,
        )
    
    @property
    def platform_name(self) -> str:
        return "fakestore"
    
    async def test_connection(self) -> bool:
        """Test connection to Fake Store API."""
        try:
            response = await self._client.get("/products?limit=1")
            return response.status_code == 200
        except Exception:
            return False
    
    async def fetch_products(
        self,
        batch_size: int = 100,
        category: Optional[str] = None,
    ) -> AsyncIterator[list[ProductData]]:
        """
        Fetch all products from Fake Store API.
        
        Note: Fake Store API doesn't have pagination, so we fetch all at once
        and yield in batches.
        """
        try:
            # Fake Store API: /products or /products/category/{category}
            if category:
                url = f"/products/category/{category}"
            else:
                url = "/products"
            
            response = await self._client.get(url)
            response.raise_for_status()
            
            products_data = response.json()
            
            # Convert to ProductData and yield in batches
            batch = []
            for item in products_data:
                product = self._parse_product(item)
                batch.append(product)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            
            # Yield remaining
            if batch:
                yield batch
                
        except httpx.HTTPError as e:
            print(f"[ERROR] Failed to fetch from Fake Store API: {e}")
            return
    
    async def fetch_product(self, product_id: str) -> Optional[ProductData]:
        """Fetch a single product by ID."""
        try:
            response = await self._client.get(f"/products/{product_id}")
            response.raise_for_status()
            
            return self._parse_product(response.json())
        except httpx.HTTPError as e:
            print(f"[ERROR] Failed to fetch product {product_id}: {e}")
            return None
    
    async def get_categories(self) -> list[str]:
        """Get all categories from Fake Store API."""
        try:
            response = await self._client.get("/products/categories")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return []
    
    async def get_total_count(self) -> int:
        """Get total product count."""
        try:
            response = await self._client.get("/products")
            response.raise_for_status()
            return len(response.json())
        except httpx.HTTPError:
            return -1
    
    def _parse_product(self, data: dict) -> ProductData:
        """Parse Fake Store API response to ProductData."""
        return ProductData(
            external_id=str(data["id"]),
            title=data.get("title", ""),
            description=data.get("description", ""),
            price=float(data.get("price", 0)),
            category=data.get("category", ""),
            image_url=data.get("image", ""),
            platform="fakestore",
            rating=data.get("rating", {}).get("rate"),
            rating_count=data.get("rating", {}).get("count"),
            in_stock=True,  # Fake Store doesn't have stock info
            attributes={
                "original_id": data["id"],
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self._client.aclose()
