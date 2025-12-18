# eaichat Project Reference

## Project Goal
Production-grade AI e-commerce platform with:
- FastAPI + Uvicorn backend
- MySQL (MetaDB) + Qdrant (vector DB)
- Multi-LLM support (OpenAI, Anthropic, Gemini, local)
- Temporal workflow orchestration
- Langfuse/LangSmith telemetry
- GDPR compliance
- Non-LLM intent fallback
- Full CI/CD with GitHub Actions

---

## Conversation Summary

### Session 1: Initial Analysis & Planning
**What was done:**
1. Analyzed existing scaffold (basic FastAPI, SQLAlchemy models, Docker Compose)
2. Identified gaps: no auth, no routers, stub scripts, no tests, no CI
3. Created `task.md` with 13 phases
4. Created `implementation_plan.md` with detailed roadmap
5. Created `CHANGELOG.md` and `SECURITY_GDPR_CHECKLIST.md`

### Session 2: Phase 1B Implementation
**What was done:**
1. Fixed Docker Compose (healthchecks, Langfuse v2.90.0, Temporal auto-setup)
2. Created GitHub Actions (ci.yaml, build.yaml, e2e.yaml)
3. Added .dockerignore files
4. Set up shadcn/ui with Tailwind CSS v3.4
5. Created product_indexer.py (Fake Store API, Qdrant integration)
6. Created Temporal workflows (ProductSync, Reindex)
7. Seeded MySQL (2 users, 3 products)
8. Committed and pushed to GitHub

**Issues Encountered:**
- Langfuse v3 requires ClickHouse → Pinned to v2.90.0
- Tailwind v4 PostCSS plugin changed → Pinned to v3.4.0
- Qdrant healthcheck used curl not available → Fixed with TCP check
- API healthcheck used curl not available → Fixed with Python urllib

---

## Current Status

### Completed Phases
| Phase | Status | Notes |
|-------|--------|-------|
| Analysis | ✅ Done | Project structure understood |
| Phase 1: Infrastructure | ✅ Done | Docker Compose, healthchecks, CI |
| Phase 1B: UI/Seeding | ✅ Done | shadcn, product indexer, Temporal |

### Pending Phases (from original plan)
| Phase | Status | Key Items |
|-------|--------|-----------|
| 2: Auth | ❌ Not Started | JWT, OAuth, RBAC |
| 3: Vector Service | ⚠️ Partial | VectorService class needed |
| 4: Multi-LLM | ❌ Not Started | OpenAI/Anthropic/Gemini adapters |
| 5: Temporal | ⚠️ Partial | Worker skeleton, needs full impl |
| 6: Chat Agent | ❌ Not Started | Chat service, SSE, tools |
| 7: Telemetry | ⚠️ Partial | Langfuse env set, SDK not configured |
| 8: Intent Fallback | ❌ Not Started | Non-LLM intent classifier |
| 9: GDPR | ❌ Not Started | Export, deletion, consent |
| 10: Frontend | ⚠️ Partial | Basic page, needs full UI |
| 11: CI/CD | ⚠️ Partial | Workflows exist, need testing |
| 12: Testing | ❌ Not Started | No tests written |
| 13: Documentation | ⚠️ Partial | README, docs incomplete |

---

## Known Issues & Fixes

### Issue Log
| ID | Issue | Fix Applied | Status |
|----|-------|-------------|--------|
| 1 | Langfuse v3 needs ClickHouse | Pinned to v2.90.0 | ✅ Fixed |
| 2 | Tailwind v4 PostCSS issue | Pinned to v3.4.0 | ✅ Fixed |
| 3 | Qdrant curl not available | TCP healthcheck | ✅ Fixed |
| 4 | API curl not available | Python urllib | ✅ Fixed |
| 5 | Temporal Postgres timing | auto-setup image | ✅ Fixed |
| 6 | Web lint errors (TS types) | Types in Docker | ⚠️ OK in container |
| 7 | Frontend latest versions | Needs update | ❌ Pending |
| 8 | Automated releases | Needs setup | ❌ Pending |
| 9 | Lint must pass | Needs validation | ❌ Pending |

---

## Next Steps (Priority Order)

### Immediate (This Session)
1. Fix frontend to use latest stable versions
2. Add automated changelog/release workflow
3. Run and fix all lint errors
4. Create comprehensive tests

### Phase 2: Authentication
- [ ] Implement JWT service
- [ ] Create auth routers
- [ ] Add password hashing
- [ ] Secure cookie handling

### Phase 3-4: LLM & Vector
- [ ] Create LLMProvider interface
- [ ] Implement provider adapters
- [ ] Create VectorService class
- [ ] Connect RAG pipeline

### Phase 5-6: Chat & Agent
- [ ] Chat workflow with Temporal
- [ ] SSE streaming
- [ ] Tool orchestration

---

## File Structure Reference

```
eaichat/
├── .github/workflows/        # CI/CD workflows
│   ├── ci.yaml              # Lint, test, security
│   ├── build.yaml           # Docker builds
│   └── e2e.yaml             # Integration tests
├── docs/
│   └── SECURITY_GDPR_CHECKLIST.md
├── server/
│   ├── app/
│   │   ├── db.py            # Database config
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── routers/         # API routers
│   │   │   └── index.py     # Product indexing
│   │   └── workflows/       # Temporal workflows
│   ├── scripts/
│   │   └── product_indexer.py  # Main indexer
│   ├── main.py              # FastAPI app
│   ├── seed.sql             # MySQL seed data
│   └── requirements-ml.txt  # ML dependencies
├── web/
│   ├── app/                 # Next.js App Router
│   ├── components/ui/       # shadcn components
│   └── lib/utils.ts
├── worker/
│   └── worker.py            # Temporal worker
├── docker-compose.yml
├── CHANGELOG.md
└── .env.example
```

---

## Commands Reference

```bash
# Start all services
docker compose up -d --build

# Run migrations
docker compose exec api python -c "from app.db import engine, Base; from app import models; Base.metadata.create_all(bind=engine)"

# Seed database
cat server/seed.sql | docker compose exec -T mysql mysql -ueaichat -psecret eaichat

# Run product indexer
docker compose exec api python scripts/product_indexer.py --fetch --index

# Check service health
curl http://localhost:8000/health
curl http://localhost:6333

# View logs
docker compose logs -f api
```

---

## Version History
| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-12-17 | Initial scaffold |
| 0.2.0 | 2025-12-18 | Phase 1B complete: shadcn, indexer, workflows |
