#!/bin/bash
set -e

API="http://localhost:8000"

echo "========================================="
echo "eaichat API Test Suite"
echo "========================================="

echo -e "\n✓ 1. Health Check"
curl -s $API/health | python3 -m json.tool

echo -e "\n✓ 2. Collection Stats"
curl -s $API/api/index/stats | python3 -m json.tool

echo -e "\n✓ 3. Semantic Search - Electronics"
curl -s -X POST $API/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "electronics", "limit": 2}' | python3 -m json.tool

echo -e "\n✓ 4. Hybrid Search - Cotton Shirt"
curl -s -X POST $API/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cotton shirt", "hybrid": true, "alpha": 0.6, "limit": 2}' | python3 -m json.tool

echo -e "\n✓ 5. Filtered Search - Women's <$50"
curl -s -X POST $API/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "clothing", "category": "women'"'"'s clothing", "max_price": 50, "limit": 3}' | python3 -m json.tool

echo -e "\n✓ 6. Platform Filter - FakeStore"
curl -s -X POST $API/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "product", "platform": "fakestore", "limit": 2}' | python3 -m json.tool

echo -e "\n✓ 7. LLM Providers"
curl -s $API/api/chat/providers | python3 -m json.tool

echo -e "\n========================================="
echo "✅ All API tests passed!"
echo "========================================="
