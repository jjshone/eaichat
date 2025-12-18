# eaichat Sprint Backlog - Phase 2

## Overview
This document tracks the comprehensive implementation roadmap based on deep analysis of current state vs goals. Updated based on user feedback on 2025-12-18.

---

## Current State Analysis

### What's Built ✅
| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose | Working | 12 services, healthchecks |
| MySQL Models | Basic | User, Product, Message, AuditLog |
| FastAPI | Minimal | Health endpoint, CORS, request ID |
| shadcn/ui | Installed | Button, Card, Input components |
| GitHub Actions | Partial | ci.yaml, build.yaml, e2e.yaml exist |
| product_indexer.py | Wrong Design | Uses MySQL as intermediary (should be direct to Qdrant) |

### Critical Issues Identified 🔴
| ID | Issue | Impact |
|----|-------|--------|
| 1 | Git workflow: commits directly to main | Need branch → PR → merge flow |
| 2 | Indexer goes: External → MySQL → Qdrant | Should be: External → Qdrant directly |
| 3 | No modular platform adapters | Can't extend to Magento, Odoo, etc. |
| 4 | Intent classification missing | No non-LLM fallback |
| 5 | HITL system missing | No human intervention workflow |
| 6 | AI providers not implemented | OpenAI/Anthropic/Gemini stubs only |
| 7 | Langfuse SDK not configured | Only env vars set |
| 8 | Temporal not fully implemented | Workflow skeletons only |
| 9 | No embeddable chat widget | User requirement |
| 10 | Automated releases not working | release-please needs proper config |

---

## Architecture Redesign

### Product Indexing (Corrected)
```
External API (Fake Store, Magento, Odoo)
          │
          ▼
   Platform Adapter (modular)
          │
          ▼
    Embedding Service
          │
          ▼
     Qdrant (vectors + payload)
          │
          ▼
    RAG Search Pipeline
```

### MySQL Role (Corrected)
MySQL stores:
- Users (auth, profiles, consent)
- Chat sessions (history, metadata)
- Audit logs (compliance)
- Connector configs (platform credentials)
- **NOT product data** (that's in Qdrant)

---

## Sprint 2 Backlog

### 2.1 Git Workflow & Releases 🏷️
- [ ] Update release.yaml for branch → PR flow
- [ ] Add conventional commits linting
- [ ] Configure release-please manifest correctly
- [ ] Add PR template

### 2.2 Modular Platform Connector Architecture 🔌
- [ ] Create `connectors/` module structure
- [ ] Define `BasePlatformConnector` abstract class
- [ ] Implement `FakeStoreConnector` (example)
- [ ] Add `MagentoConnector` stub
- [ ] Add `OdooConnector` stub
- [ ] Each connector: fetch products with images → embeddings → Qdrant

### 2.3 Qdrant Vector Service (Production) 📊
- [ ] Create `VectorService` class with full API
- [ ] Collection schema with named vectors (text + image)
- [ ] Hybrid search (dense + sparse)
- [ ] Batch upsert with Temporal
- [ ] Scheduled sync via Temporal cron
- [ ] Payload indexing for filters
- [ ] Image URL storage in payload

### 2.4 AI Provider Integration 🤖
- [ ] Create `BaseLLMProvider` abstract class
- [ ] Implement `OpenAIProvider`
- [ ] Implement `AnthropicProvider`
- [ ] Implement `GeminiProvider`
- [ ] Add failover/circuit breaker
- [ ] Add rate limiting per provider
- [ ] Provider selection strategy

### 2.5 Langfuse Telemetry 📈
- [ ] Initialize Langfuse client properly
- [ ] Wrap LLM calls with traces
- [ ] Log tool executions
- [ ] Track RAG retrieval scores
- [ ] Create Langfuse org/project
- [ ] Dashboard setup

### 2.6 Temporal Full Implementation 🔄
- [ ] Configure Temporal client
- [ ] `ProductSyncWorkflow` with batching
- [ ] `ChatWorkflow` for RAG orchestration
- [ ] Scheduled cron for periodic sync
- [ ] Worker with proper activity registration
- [ ] Retry policies and timeouts

### 2.7 Intent Classification System 🎯
- [ ] Create `IntentClassifier` service
- [ ] Rule-based classification (keywords)
- [ ] ML classification (SentenceTransformer + cosine)
- [ ] Intent training data (JSON fixtures)
- [ ] Canned response system
- [ ] LLM/Intent mode toggle endpoint

### 2.8 LLM Tool Calling (Actionable) 🔧
- [ ] Define tool schemas (OpenAPI-style)
- [ ] `search_products` tool
- [ ] `add_to_cart` tool
- [ ] `get_order_status` tool (example API call)
- [ ] Tool execution engine
- [ ] Response formatting

### 2.9 HITL (Human-in-the-Loop) 👤
- [ ] Create HITL workflow in Temporal
- [ ] Escalation trigger conditions
- [ ] Admin notification system
- [ ] Human takeover endpoint
- [ ] Handback mechanism
- [ ] Escalation queue UI

### 2.10 Embeddable Chat Widget 💬
- [ ] Create standalone widget bundle
- [ ] Iframe/script embed options
- [ ] Customization API (colors, position)
- [ ] WebSocket/SSE connection
- [ ] Session management
- [ ] Widget documentation

### 2.11 Frontend RAG Integration 🖥️
- [ ] Chat interface component
- [ ] Real-time streaming responses
- [ ] Product cards in responses
- [ ] Message history
- [ ] LLM/Intent mode selector
- [ ] Connection status indicator

### 2.12 MySQL Schema Improvements 🗃️
- [ ] Add `ChatSession` model
- [ ] Add `UserConsent` model (GDPR)
- [ ] Add `ConnectorConfig` model (platform credentials)
- [ ] Add `CartItem` model
- [ ] Add GDPR fields to User (consent_at, deleted_at)
- [ ] Create proper migrations

### 2.13 Authentication 🔐
- [ ] JWT service (access + refresh)
- [ ] Auth routers (/login, /register, /refresh)
- [ ] Password hashing (argon2)
- [ ] RBAC middleware
- [ ] Secure cookie handling

---

## Qdrant Schema Design

### products Collection
```json
{
  "name": "products",
  "vectors": {
    "text": { "size": 384, "distance": "Cosine" },
    "image": { "size": 512, "distance": "Cosine" }
  },
  "payload_schema": {
    "product_id": "keyword",
    "title": "text",
    "description": "text",
    "price": "float",
    "category": "keyword",
    "image_url": "keyword",
    "platform": "keyword",
    "rating": "float",
    "in_stock": "bool",
    "updated_at": "datetime"
  }
}
```

### intents Collection (for classification)
```json
{
  "name": "intents",
  "vectors": { "size": 384, "distance": "Cosine" },
  "payload_schema": {
    "intent": "keyword",
    "examples": "text[]",
    "response_template": "text"
  }
}
```

---

## File Structure (Target)

```
server/
├── app/
│   ├── connectors/           # Platform adapters
│   │   ├── __init__.py
│   │   ├── base.py           # BasePlatformConnector
│   │   ├── fakestore.py
│   │   ├── magento.py
│   │   └── odoo.py
│   ├── providers/            # LLM providers
│   │   ├── __init__.py
│   │   ├── base.py           # BaseLLMProvider
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── gemini.py
│   ├── services/
│   │   ├── vector_service.py
│   │   ├── embedding_service.py
│   │   ├── intent_service.py
│   │   ├── auth_service.py
│   │   └── hitl_service.py
│   ├── tools/                # LLM tool definitions
│   │   ├── __init__.py
│   │   ├── search_products.py
│   │   └── cart_actions.py
│   ├── workflows/            # Temporal
│   │   ├── sync_workflow.py
│   │   ├── chat_workflow.py
│   │   └── hitl_workflow.py
│   └── routers/
│       ├── auth.py
│       ├── chat.py
│       ├── products.py
│       └── admin.py
```

---

## Implementation Order

1. **Git Workflow** (prerequisite for all else)
2. **Modular Connectors** + **VectorService** 
3. **AI Providers** + **Langfuse**
4. **Temporal Full Implementation**
5. **Intent Classification** + **Tool Calling**
6. **HITL System**
7. **Frontend RAG**
8. **Embeddable Widget**
9. **Auth** + **MySQL Schema**
10. **Testing** + **Documentation**

---

## Notes for Implementation

### Do NOT:
- Store products in MySQL (use Qdrant payloads)
- Commit directly to main (use branches)
- Use placeholder/stub code (implement fully)

### DO:
- Create feature branches for each sprint item
- Write modular, extensible code
- Include proper error handling
- Add logging with Langfuse
- Write tests for each component
