"""
Magento 2 Platform Connector (Stub)
===================================

Connector for Magento 2 REST API.
Requires API integration token from Magento admin.

Configuration required:
- base_url: Magento store URL (e.g., https://your-store.com/rest/V1)
- api_key: Integration access token
- store_id: Store view code (optional, defaults to 'default')
"""

import httpx
from typing import AsyncIterator, Optional

from . import BasePlatformConnector, ProductData, ConnectorConfig


class MagentoConnector(BasePlatformConnector):
    """Connector for Magento 2 REST API."""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
    
    @property
    def platform_name(self) -> str:
        return "magento"
    
    async def test_connection(self) -> bool:
        """Test connection to Magento API."""
        try:
            # Test with store config endpoint
            response = await self._client.get("/store/storeConfigs")
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Magento connection test failed: {e}")
            return False
    
    async def fetch_products(
        self,
        batch_size: int = 100,
        category: Optional[str] = None,
    ) -> AsyncIterator[list[ProductData]]:
        """
        Fetch products from Magento 2 using search criteria.
        
        Magento API: GET /products?searchCriteria[pageSize]=N&searchCriteria[currentPage]=P
        """
        page = 1
        
        while True:
            try:
                params = {
                    "searchCriteria[pageSize]": batch_size,
                    "searchCriteria[currentPage]": page,
                }
                
                if category:
                    params["searchCriteria[filter_groups][0][filters][0][field]"] = "category_id"
                    params["searchCriteria[filter_groups][0][filters][0][value]"] = category
                
                response = await self._client.get("/products", params=params)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break
                
                batch = [self._parse_product(item) for item in items]
                yield batch
                
                # Check if more pages
                total_count = data.get("total_count", 0)
                if page * batch_size >= total_count:
                    break
                
                page += 1
                
            except httpx.HTTPError as e:
                print(f"[ERROR] Magento fetch failed: {e}")
                break
    
    async def fetch_product(self, product_id: str) -> Optional[ProductData]:
        """Fetch single product by SKU."""
        try:
            response = await self._client.get(f"/products/{product_id}")
            response.raise_for_status()
            return self._parse_product(response.json())
        except httpx.HTTPError:
            return None
    
    async def get_categories(self) -> list[str]:
        """Get category tree from Magento."""
        try:
            response = await self._client.get("/categories")
            response.raise_for_status()
            
            categories = []
            self._extract_categories(response.json(), categories)
            return categories
        except httpx.HTTPError:
            return []
    
    def _extract_categories(self, node: dict, categories: list[str]):
        """Recursively extract category names."""
        if node.get("name"):
            categories.append(node["name"])
        
        for child in node.get("children_data", []):
            self._extract_categories(child, categories)
    
    def _parse_product(self, data: dict) -> ProductData:
        """Parse Magento product to ProductData."""
        # Find custom attributes
        custom_attrs = {
            attr["attribute_code"]: attr["value"]
            for attr in data.get("custom_attributes", [])
        }
        
        # Get image URL from media gallery
        media = data.get("media_gallery_entries", [])
        image_url = ""
        if media:
            # Construct full URL (need store base URL)
            image_file = media[0].get("file", "")
            if image_file:
                image_url = f"{self.config.base_url}/pub/media/catalog/product{image_file}"
        
        return ProductData(
            external_id=data.get("sku", str(data.get("id", ""))),
            title=data.get("name", ""),
            description=custom_attrs.get("description", "")[:1000] if custom_attrs.get("description") else "",
            price=float(data.get("price", 0)),
            category=str(data.get("category_ids", [""])[0]) if data.get("category_ids") else "",
            image_url=image_url,
            platform="magento",
            in_stock=data.get("status") == 1,
            sku=data.get("sku"),
            brand=custom_attrs.get("manufacturer"),
            attributes={
                "type_id": data.get("type_id"),
                "visibility": data.get("visibility"),
                "weight": data.get("weight"),
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self._client.aclose()
