# eaichat API Documentation

Complete guide for integrating with the eaichat platform.

**Base URL:** `http://localhost:8000`

---

## Table of Contents
- [Quick Start](#quick-start)
- [Indexing APIs](#indexing-apis)
- [Search APIs](#search-apis)
- [Chat APIs](#chat-apis)
- [Integration Guide](#integration-guide)
- [Testing](#testing)

---

## Quick Start

### Check System Health
\`\`\`bash
curl http://localhost:8000/health
\`\`\`

### Create Collection & Sync Products
\`\`\`bash
# 1. Create collection
curl -X POST http://localhost:8000/api/index/create-collection

# 2. Sync from FakeStore API
curl -X POST http://localhost:8000/api/index/sync \\
  -H "Content-Type: application/json" \\
  -d '{"platform": "fakestore", "batch_size": 10}'

# 3. Check stats
curl http://localhost:8000/api/index/stats

# 4. Search products
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "laptop", "limit": 5}'
\`\`\`

---

## Indexing APIs

### Create Collection
\`\`\`bash
curl -X POST http://localhost:8000/api/index/create-collection
\`\`\`

**Recreate (delete existing):**
\`\`\`bash
curl -X POST http://localhost:8000/api/index/create-collection \\
  -H "Content-Type: application/json" \\
  -d '{"recreate": true}'
\`\`\`

### Sync Products via Temporal
\`\`\`bash
curl -X POST http://localhost:8000/api/index/sync \\
  -H "Content-Type: application/json" \\
  -d '{
    "platform": "fakestore",
    "batch_size": 20
  }'
\`\`\`

**Response:**
\`\`\`json
{
  "status": "started",
  "message": "Indexing from fakestore started via Temporal",
  "job_id": "product-sync-fakestore-abc123"
}
\`\`\`

**Monitor:** http://localhost:8088 (Temporal UI)

### Collection Stats
\`\`\`bash
curl http://localhost:8000/api/index/stats
\`\`\`

---

## Search APIs

### Semantic Search
\`\`\`bash
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "blue jacket for women",
    "limit": 5
  }'
\`\`\`

### Hybrid Search (Vector + Keyword)
\`\`\`bash
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "cotton shirt",
    "limit": 3,
    "hybrid": true,
    "alpha": 0.6
  }'
\`\`\`

### Filtered Search

**By Category:**
\`\`\`bash
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "shirt",
    "category": "men'"'"'s clothing",
    "limit": 5
  }'
\`\`\`

**By Price:**
\`\`\`bash
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "electronics",
    "min_price": 100,
    "max_price": 500,
    "limit": 3
  }'
\`\`\`

**Combined:**
\`\`\`bash
curl -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "dress",
    "category": "women'"'"'s clothing",
    "platform": "fakestore",
    "max_price": 50,
    "limit": 10
  }'
\`\`\`

---

## Chat APIs

### Send Message
\`\`\`bash
curl -X POST http://localhost:8000/api/chat/send \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Show me affordable jackets",
    "use_rag": true
  }'
\`\`\`

### List Providers
\`\`\`bash
curl http://localhost:8000/api/chat/providers
\`\`\`

---

## Integration Guide

### Creating a Custom Connector

1. **Create connector file:** `server/app/connectors/myplatform.py`

2. **Implement BaseConnector:**
\`\`\`python
from app.connectors import BaseConnector, ProductData

class MyPlatformConnector(BaseConnector):
    async def fetch_products(self, batch_size: int = 50):
        # Fetch from your API
        products = await self._fetch_from_api()
        
        # Convert to ProductData
        yield [
            ProductData(
                external_id=str(p["id"]),
                title=p["name"],
                description=p["desc"],
                price=float(p["price"]),
                category=p.get("category"),
                platform="myplatform"
            )
            for p in products
        ]
\`\`\`

3. **Register in** `server/app/connectors/__init__.py`

4. **Sync:**
\`\`\`bash
curl -X POST http://localhost:8000/api/index/sync \\
  -d '{"platform": "myplatform", "batch_size": 20}'
\`\`\`

---

## Testing

### Full Test Script
\`\`\`bash
#!/bin/bash

echo "1. Health"
curl -s http://localhost:8000/health | python3 -m json.tool

echo "2. Create Collection"
curl -s -X POST http://localhost:8000/api/index/create-collection

echo "3. Sync (batch_size=10)"
curl -s -X POST http://localhost:8000/api/index/sync \\
  -H "Content-Type: application/json" \\
  -d '{"platform": "fakestore", "batch_size": 10}'

echo "4. Wait 60s..."
sleep 60

echo "5. Stats"
curl -s http://localhost:8000/api/index/stats | python3 -m json.tool

echo "6. Search"
curl -s -X POST http://localhost:8000/api/index/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "electronics", "limit": 3}' | python3 -m json.tool
\`\`\`

---

## Monitoring

- **Temporal UI:** http://localhost:8088
- **Qdrant Dashboard:** http://localhost:6333/dashboard  
- **Langfuse:** http://localhost:8081
- **phpMyAdmin:** http://localhost:8080

**Logs:**
\`\`\`bash
docker compose logs worker --follow
\`\`\`
