# eaichat

Production-grade AI scaffold (FastAPI + Qdrant + MySQL + Temporal + Next.js)

Quickstart (local dev)

This repository contains a scaffold for a production-grade AI app using FastAPI, Qdrant, MySQL, Temporal, and a Next.js frontend.

To run the basic scaffold via Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Services available after `docker compose up` (local):

- API: http://localhost:8000/health
- Frontend: http://localhost:3000
- phpMyAdmin: http://localhost:8080
- Qdrant: http://localhost:6333

Files added in this scaffold:

- `server/` - FastAPI server skeleton
- `worker/` - background worker skeleton
- `web/` - Next.js frontend skeleton
- `docker-compose.yml` - local dev compose file
- `scripts/reindex_qdrant.py` - reindex CLI stub

Next steps: implement models, migrations (Alembic), vector service, LLM providers, Temporal workflows, and CI configuration.
