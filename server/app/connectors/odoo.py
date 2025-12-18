"""
Odoo Platform Connector (Stub)
==============================

Connector for Odoo ERP via XML-RPC or JSON-RPC API.
Requires Odoo user credentials with API access.

Configuration required:
- base_url: Odoo instance URL (e.g., https://your-company.odoo.com)
- api_key: User API key or password
- extra["database"]: Odoo database name
- extra["username"]: Odoo username
"""

import httpx
from typing import AsyncIterator, Optional

from . import BasePlatformConnector, ProductData, ConnectorConfig


class OdooConnector(BasePlatformConnector):
    """Connector for Odoo ERP via JSON-RPC."""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.database = config.extra.get("database", "")
        self.username = config.extra.get("username", "")
        self._uid: Optional[int] = None
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=60.0,
        )
    
    @property
    def platform_name(self) -> str:
        return "odoo"
    
    async def _authenticate(self) -> bool:
        """Authenticate with Odoo and get user ID."""
        if self._uid is not None:
            return True
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.database, self.username, self.config.api_key, {}],
                },
                "id": 1,
            }
            
            response = await self._client.post("/jsonrpc", json=payload)
            response.raise_for_status()
            
            result = response.json()
            self._uid = result.get("result")
            return self._uid is not None
        except Exception as e:
            print(f"[ERROR] Odoo authentication failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Odoo."""
        return await self._authenticate()
    
    async def _execute_kw(
        self,
        model: str,
        method: str,
        args: list,
        kwargs: Optional[dict] = None,
    ) -> Optional[any]:
        """Execute Odoo model method via JSON-RPC."""
        if not await self._authenticate():
            return None
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.database,
                    self._uid,
                    self.config.api_key,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
            "id": 2,
        }
        
        try:
            response = await self._client.post("/jsonrpc", json=payload)
            response.raise_for_status()
            return response.json().get("result")
        except Exception as e:
            print(f"[ERROR] Odoo execute_kw failed: {e}")
            return None
    
    async def fetch_products(
        self,
        batch_size: int = 100,
        category: Optional[str] = None,
    ) -> AsyncIterator[list[ProductData]]:
        """Fetch products from Odoo product.template model."""
        offset = 0
        
        while True:
            # Build domain filter
            domain = [("sale_ok", "=", True)]
            if category:
                domain.append(("categ_id.name", "ilike", category))
            
            # Fetch batch
            products = await self._execute_kw(
                "product.template",
                "search_read",
                [domain],
                {
                    "fields": [
                        "id", "name", "description_sale", "list_price",
                        "categ_id", "image_1920", "default_code", "qty_available"
                    ],
                    "limit": batch_size,
                    "offset": offset,
                }
            )
            
            if not products:
                break
            
            batch = [self._parse_product(p) for p in products]
            yield batch
            
            if len(products) < batch_size:
                break
            
            offset += batch_size
    
    async def fetch_product(self, product_id: str) -> Optional[ProductData]:
        """Fetch single product by ID."""
        products = await self._execute_kw(
            "product.template",
            "search_read",
            [[("id", "=", int(product_id))]],
            {
                "fields": [
                    "id", "name", "description_sale", "list_price",
                    "categ_id", "image_1920", "default_code", "qty_available"
                ],
            }
        )
        
        if products:
            return self._parse_product(products[0])
        return None
    
    async def get_categories(self) -> list[str]:
        """Get product categories from Odoo."""
        categories = await self._execute_kw(
            "product.category",
            "search_read",
            [[]],
            {"fields": ["name"]},
        )
        
        if categories:
            return [c["name"] for c in categories]
        return []
    
    def _parse_product(self, data: dict) -> ProductData:
        """Parse Odoo product to ProductData."""
        # Category comes as [id, name] tuple
        category = ""
        if data.get("categ_id"):
            category = data["categ_id"][1] if isinstance(data["categ_id"], list) else str(data["categ_id"])
        
        # Image is base64 encoded, we'll store a reference URL instead
        # In production, you'd serve this through an image endpoint
        image_url = ""
        if data.get("image_1920"):
            image_url = f"{self.config.base_url}/web/image/product.template/{data['id']}/image_1920"
        
        return ProductData(
            external_id=str(data["id"]),
            title=data.get("name", ""),
            description=data.get("description_sale") or "",
            price=float(data.get("list_price", 0)),
            category=category,
            image_url=image_url,
            platform="odoo",
            in_stock=data.get("qty_available", 0) > 0,
            sku=data.get("default_code"),
            attributes={
                "qty_available": data.get("qty_available", 0),
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self._client.aclose()
