from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid

app = FastAPI(
    title="eaichat-api",
    description="Production-grade AI E-commerce API",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


class HealthResponse(BaseModel):
    status: str
    version: str | None = None
    services: dict | None = None


@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    return HealthResponse(
        status="ok",
        version=os.getenv("EAICHAT_VERSION", "0.1.0"),
        services={
            "mysql": "configured",
            "redis": "configured",
            "qdrant": "configured",
            "temporal": "configured",
            "langfuse": "configured",
        }
    )


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


# Include routers
try:
    from app.routers import index_router
    app.include_router(index_router)
except ImportError as e:
    print(f"[WARN] Could not load index router: {e}")
