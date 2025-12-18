# eaichat API - Quick Reference

## Base URL
```
http://localhost:8000
```

## Quick Start

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Create Collection
```bash
curl -X POST http://localhost:8000/api/index/create-collection
```

### 3. Sync Products
```bash
curl -X POST http://localhost:8000/api/index/sync \
  -H "Content-Type: application/json" \
  -d '{"platform": "fakestore", "batch_size": 10}'
```

### 4. Search Products
```bash
curl -X POST http://localhost:8000/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "jacket", "limit": 5}'
```

## Full Documentation

See `/home/hp/Pictures/rnd/eaichat/docs/API_FULL.md` for complete details.
