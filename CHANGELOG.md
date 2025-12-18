# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Production-grade redesign with FastAPI + Uvicorn
- Multi-LLM provider support (OpenAI, Anthropic, Gemini)
- Qdrant vector database integration with full reindex scripts
- Temporal workflow orchestration
- Langfuse/LangSmith telemetry
- GDPR compliance (data export, deletion, consent)
- GitHub Actions CI/CD
- Comprehensive test suite

## [0.1.0] - 2025-12-17

### Added
- Initial scaffold created
- **Docker Compose** with 9 services:
  - MySQL 8.0 with phpMyAdmin
  - Redis 7
  - Qdrant (vector database)
  - Temporal server with UI
  - Langfuse (observability)
  - PostgreSQL (for Langfuse)
  - API (FastAPI)
  - Worker (placeholder)
  - Web (Next.js)
- **FastAPI Server** with basic endpoints:
  - `GET /health` - Health check
  - `GET /ping` - Ping/pong
- **SQLAlchemy Models**:
  - User (email, password, is_active, is_admin)
  - Product (title, description, price, category)
  - Message (user_id, role, content)
  - AuditLog (request tracking with PII flag)
  - ReindexCheckpoint (for vector reindex resumption)
- **Alembic Migrations** - Initial migration creating all tables
- **Reindex Script** - Stub for Qdrant reindexing (`scripts/reindex_qdrant.py`)
- **Environment Configuration** - `.env.example` with all service variables

### Notes
- This is a scaffold only - most services are placeholders
- Authentication not yet implemented
- LLM providers not yet integrated
- Worker does not connect to Temporal
- Frontend has no pages

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2025-12-17 | Initial scaffold |
