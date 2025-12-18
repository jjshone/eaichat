# eaichat

**Production-grade AI E-commerce Chat Platform**

FastAPI + Qdrant + MySQL + Temporal + Next.js + Multi-LLM Support

[![CI](https://github.com/jjshone/eaichat/actions/workflows/ci.yaml/badge.svg)](https://github.com/jjshone/eaichat/actions/workflows/ci.yaml)
[![Release](https://github.com/jjshone/eaichat/actions/workflows/release.yaml/badge.svg)](https://github.com/jjshone/eaichat/actions/workflows/release.yaml)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose v2+
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/jjshone/eaichat.git
cd eaichat

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d --build

# Wait for services to be healthy (about 30-60 seconds)
docker compose ps

# Verify API is running
curl http://localhost:8000/health
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | FastAPI backend |
| **Frontend** | http://localhost:3000 | Next.js web app |
| **Qdrant** | http://localhost:6333 | Vector database UI |
| **Temporal UI** | http://localhost:8088 | Workflow management |
| **Langfuse** | http://localhost:3001 | LLM observability |
| **phpMyAdmin** | http://localhost:8080 | MySQL management |

---

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                        │
│                    (shadcn/ui, Tailwind CSS)                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Chat Router  │  │ Index Router │  │ Auth Router  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Services Layer                         │   │
│  │  • IndexingService    • EmbeddingService                 │   │
│  │  • IntentService      • HITLService                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Connectors  │  │  Providers   │  │    Tools     │           │
│  │ (FakeStore,  │  │  (OpenAI,    │  │ (search,     │           │
│  │  Magento,    │  │  Anthropic,  │  │  cart, etc.) │           │
│  │  Odoo)       │  │  Gemini)     │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐         ┌──────────┐         ┌──────────┐
   │  Qdrant  │         │  MySQL   │         │ Temporal │
   │ (vectors)│         │ (users,  │         │(workflows)│
   │          │         │  logs)   │         │          │
   └──────────┘         └──────────┘         └──────────┘
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Vector Database (Qdrant or Typesense)
VECTOR_DB_BACKEND=qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# LLM Providers (configure at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEFAULT_LLM_PROVIDER=openai

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Authentication
JWT_SECRET_KEY=your-secret-key
```

See [`.env.example`](.env.example) for all options.

---

## 🏗️ Project Structure

```
eaichat/
├── .github/
│   └── workflows/          # CI/CD workflows
│       ├── ci.yaml         # Lint, test, security scan
│       ├── build.yaml      # Docker image builds
│       ├── e2e.yaml        # End-to-end tests
│       └── release.yaml    # Automated releases
├── docs/
│   ├── PROJECT_REFERENCE.md
│   ├── SPRINT_BACKLOG.md
│   └── SECURITY_GDPR_CHECKLIST.md
├── server/                 # FastAPI Backend
│   ├── app/
│   │   ├── connectors/     # Platform adapters (FakeStore, Magento, Odoo)
│   │   ├── providers/      # LLM providers (OpenAI, Anthropic, Gemini)
│   │   ├── services/       # Business logic
│   │   ├── vectordb/       # Vector DB abstraction (Qdrant, Typesense)
│   │   ├── workflows/      # Temporal workflows
│   │   ├── routers/        # API endpoints
│   │   ├── models.py       # SQLAlchemy models
│   │   └── db.py           # Database config
│   ├── scripts/            # CLI tools
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── web/                    # Next.js Frontend
│   ├── app/                # App Router pages
│   ├── components/
│   │   └── ui/             # shadcn/ui components
│   └── lib/
├── worker/                 # Temporal Worker
├── docker-compose.yml
├── CHANGELOG.md
└── README.md
```

---

## 🔄 Development Workflow

### Git Workflow

We use conventional commits and feature branches:

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes with conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"

# Push and create PR
git push -u origin feature/my-feature
```

### Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `refactor` | Code refactoring |
| `test` | Tests |
| `ci` | CI/CD changes |
| `chore` | Maintenance |

### Automated Releases

On merge to `main`:
1. **release-please** creates a Release PR with changelog
2. Merge the Release PR to:
   - Create a GitHub Release
   - Tag the version
   - Build and push Docker images to GHCR

---

## 🐳 Docker Commands

```bash
# Start all services
docker compose up -d

# Rebuild specific service
docker compose up -d --build api

# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Clean up (including volumes)
docker compose down -v
```

---

## 🔌 API Endpoints

### Product Indexing

```bash
# Sync products from platform to vector DB
curl -X POST http://localhost:8000/api/index/sync \
  -H "Content-Type: application/json" \
  -d '{"platform": "fakestore", "batch_size": 50}'

# Search products (RAG)
curl -X POST http://localhost:8000/api/index/search \
  -H "Content-Type: application/json" \
  -d '{"query": "blue winter jacket", "limit": 5}'

# Get collection stats
curl http://localhost:8000/api/index/stats
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🧪 Testing

```bash
# Run Python tests
docker compose exec api pytest tests/ -v

# Run frontend lint
cd web && npm run lint

# Run all CI checks locally
docker compose run --rm api ruff check server/
docker compose run --rm api bandit -r server/ -ll
```

---

## 🚀 Production Deployment

### With Docker Compose

```bash
# Set production environment
export APP_ENV=production
export APP_DEBUG=false

# Use production compose file (create if needed)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Considerations

1. **TLS/HTTPS**: Use reverse proxy (nginx, Traefik)
2. **Secrets**: Use secret manager (Vault, AWS Secrets)
3. **Database**: External managed MySQL/Postgres
4. **Vector DB**: Qdrant Cloud or self-hosted cluster
5. **Monitoring**: Langfuse + Prometheus + Grafana

---

## 📖 Documentation

- [Project Reference](docs/PROJECT_REFERENCE.md) - Project overview and status
- [Sprint Backlog](docs/SPRINT_BACKLOG.md) - Current development roadmap
- [Security Checklist](docs/SECURITY_GDPR_CHECKLIST.md) - Security and GDPR compliance

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit with conventional commits (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary. All rights reserved.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Qdrant](https://qdrant.tech/) - Vector database
- [Temporal](https://temporal.io/) - Workflow orchestration
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [Langfuse](https://langfuse.com/) - LLM observability
