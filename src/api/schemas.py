"""Pydantic schemas for the Marketing Intelligence API."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    thread_id: str | None = None


class SourceItem(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""


class QueryResponse(BaseModel):
    thread_id: str
    plan: list[str] = []
    final_answer: str = ""
    charts: list[str] = []
    sources: list[SourceItem] = []
    awaiting_approval: bool = False


class ApproveRequest(BaseModel):
    thread_id: str
    plan: list[str] | None = None


class StreamEvent(BaseModel):
    event: str  # node_start, node_end, done, error
    node: str = ""
    data: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.2.0"
