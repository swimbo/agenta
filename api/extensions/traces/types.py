"""
Agent Matrix - Traces Types

Pydantic models for trace/span operations.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AgentMatrixSpanType(str, Enum):
    """Agent Matrix span types."""
    SESSION = "session"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    EVALUATION = "evaluation"
    MESSAGE = "message"
    CUSTOM = "custom"


class AgentaSpanType(str, Enum):
    """Agenta's native span types."""
    AGENT = "agent"
    TOOL = "tool"
    LLM = "llm"
    TASK = "task"
    CHAIN = "chain"
    WORKFLOW = "workflow"
    EMBEDDING = "embedding"
    RETRIEVER = "retriever"
    RERANKER = "reranker"


# Mapping from Agent Matrix span types to Agenta span types
SPAN_TYPE_MAPPING = {
    AgentMatrixSpanType.SESSION: AgentaSpanType.AGENT,
    AgentMatrixSpanType.TOOL_CALL: AgentaSpanType.TOOL,
    AgentMatrixSpanType.LLM_CALL: AgentaSpanType.LLM,
    AgentMatrixSpanType.EVALUATION: AgentaSpanType.TASK,
    AgentMatrixSpanType.MESSAGE: AgentaSpanType.CHAIN,
    AgentMatrixSpanType.CUSTOM: AgentaSpanType.WORKFLOW,
}


class SpanCreate(BaseModel):
    """Create a new span."""
    trace_id: UUID = Field(..., description="Session/trace ID")
    span_type: AgentMatrixSpanType
    name: str
    parent_span_id: Optional[UUID] = None
    input: Optional[dict[str, Any]] = None
    output: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = "ok"
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[float] = None
    model: Optional[str] = None


class SpanUpdate(BaseModel):
    """Update an existing span."""
    output: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[float] = None


class Span(BaseModel):
    """Span response model."""
    id: UUID
    trace_id: UUID
    parent_span_id: Optional[UUID] = None
    span_type: str
    name: str
    input: Optional[dict[str, Any]] = None
    output: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "ok"
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[float] = None
    model: Optional[str] = None
    children: list["Span"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TraceTree(BaseModel):
    """Hierarchical trace tree response."""
    trace_id: UUID
    spans: list[Span]
    total_spans: int
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost: float = 0.0
    duration_ms: Optional[int] = None


class TraceQuery(BaseModel):
    """Query parameters for listing traces."""
    project_id: UUID
    session_id: Optional[UUID] = None
    span_type: Optional[AgentMatrixSpanType] = None
    status: Optional[str] = None
    start_time_gte: Optional[datetime] = None
    start_time_lte: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = 0
