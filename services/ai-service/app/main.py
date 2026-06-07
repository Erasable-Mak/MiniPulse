"""MiniPulse AI Service - FastAPI application entry point with lifespan management."""

import structlog
from typing import Union
from fastapi import FastAPI
from contextlib import asynccontextmanager
from groq import AsyncGroq

from app.config import settings
from app.logging import setup_logging
from app.clients.hubspot import HubSpotClient
from app.memory import ThreadMemory
from app.models import QueryRequest, QueryResponse, ErrorResponse
from app.orchestrator import Orchestrator

setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

hubspot_client = None
thread_memory = None
groq_client = None
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared clients and orchestrator on startup, teardown on shutdown."""
    global hubspot_client, thread_memory, groq_client, orchestrator

    hubspot_client = HubSpotClient(settings.HUBSPOT_ACCESS_TOKEN)
    thread_memory = ThreadMemory()
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    orchestrator = Orchestrator(hubspot_client, thread_memory, groq_client)

    logger.info("ai_service_started")
    yield
    logger.info("ai_service_stopped")

app = FastAPI(title="MiniPulse AI Service", version="0.1.0", lifespan=lifespan)

@app.post("/api/query", response_model=Union[QueryResponse, ErrorResponse])
async def process_query_endpoint(request: QueryRequest):
    """Accept a CRM query, route it through the LLM orchestrator, and return the result."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request.request_id)

    try:
        result = await orchestrator.process_query(
            query=request.query,
            thread_id=request.thread_id,
            request_id=request.request_id
        )
        return result
    finally:
        structlog.contextvars.clear_contextvars()

@app.get("/healthz")
async def healthz() -> dict:
    """Liveness probe for container orchestration."""
    return {"status": "healthy", "service": "ai-service"}
