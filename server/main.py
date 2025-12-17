from fastapi import FastAPI, Request
from pydantic import BaseModel
import os

app = FastAPI(title="eaichat-api")


class HealthResponse(BaseModel):
    status: str
    version: str | None = None


@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    return HealthResponse(status="ok", version=os.getenv("EAICHAT_VERSION"))


@app.get("/ping")
async def ping():
    return {"ping": "pong"}
