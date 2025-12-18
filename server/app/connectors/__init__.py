"""
Platform Connectors Module
==========================

Provides modular adapters for fetching product data from various platforms.
Each connector implements BasePlatformConnector and handles:
- Authentication with the platform
- Fetching products (paginated)
- Transforming to unified ProductData format
- Image URL extraction

Usage:
    from app.connectors import get_connector
    
    connector = get_connector("fakestore")  # or "magento", "odoo"
    async for batch in connector.fetch_products(batch_size=100):
        # batch is list[ProductData]
        await index_products(batch)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional
from enum import Enum


class PlatformType(Enum):
    FAKESTORE = "fakestore"
    MAGENTO = "magento"
    ODOO = "odoo"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"


@dataclass
class ProductData:
    """Unified product data format from any platform."""
    external_id: str
    title: str
    description: str
    price: float
    category: str
    image_url: str
    platform: str
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    in_stock: bool = True
    sku: Optional[str] = None
    brand: Optional[str] = None
    attributes: dict = field(default_factory=dict)  # Platform-specific attributes


@dataclass
class ConnectorConfig:
    """Configuration for a platform connector."""
    platform: PlatformType
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    store_id: Optional[str] = None
    extra: dict = field(default_factory=dict)


class BasePlatformConnector(ABC):
    """Abstract base class for platform connectors."""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connectivity to the platform."""
        pass
    
    @abstractmethod
    async def fetch_products(
        self,
        batch_size: int = 100,
        category: Optional[str] = None,
    ) -> AsyncIterator[list[ProductData]]:
        """
        Fetch products from platform in batches.
        
        Yields:
            Batches of ProductData objects
        """
        pass
    
    @abstractmethod
    async def fetch_product(self, product_id: str) -> Optional[ProductData]:
        """Fetch a single product by ID."""
        pass
    
    @abstractmethod
    async def get_categories(self) -> list[str]:
        """Get list of available categories."""
        pass
    
    async def get_total_count(self) -> int:
        """Get total product count (optional implementation)."""
        return -1  # -1 means unknown


def get_connector(platform: str, config: Optional[ConnectorConfig] = None) -> BasePlatformConnector:
    """Factory function to get a platform connector."""
    platform_type = PlatformType(platform.lower())
    
    if platform_type == PlatformType.FAKESTORE:
        from .fakestore import FakeStoreConnector
        return FakeStoreConnector(config or ConnectorConfig(
            platform=PlatformType.FAKESTORE,
            base_url="https://fakestoreapi.com",
        ))
    elif platform_type == PlatformType.MAGENTO:
        from .magento import MagentoConnector
        if not config:
            raise ValueError("Magento connector requires configuration")
        return MagentoConnector(config)
    elif platform_type == PlatformType.ODOO:
        from .odoo import OdooConnector
        if not config:
            raise ValueError("Odoo connector requires configuration")
        return OdooConnector(config)
    else:
        raise ValueError(f"Unknown platform: {platform}")
