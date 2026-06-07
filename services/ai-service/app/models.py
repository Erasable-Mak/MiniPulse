"""Pydantic models for the AI Service API request and response schemas."""

from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    """Incoming query payload from the Slack adapter."""
    query: str
    thread_id: str
    request_id: str

class QueryResponse(BaseModel):
    """Successful response containing the LLM-generated answer."""
    answer: str
    source: str
    tools_used: List[str]
    duration_ms: int
    request_id: str

class ErrorResponse(BaseModel):
    """Error response returned when the orchestrator encounters a failure."""
    error: str
    message: str
    request_id: str
