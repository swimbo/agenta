"""
Agent Matrix - Sessions Types

Pydantic models for session DTOs and request/response types.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class SessionType(str, Enum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    OVERNIGHT = "overnight"
    PROMPTS = "prompts"
    TEST = "test"
    INTERACTIVE = "interactive"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# -----------------------------------------------------------------------------
# Session DTOs
# -----------------------------------------------------------------------------

class SessionCreate(BaseModel):
    """DTO for creating a session."""
    agent_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    parent_session_id: Optional[UUID] = None
    meta_session_id: Optional[UUID] = None
    session_type: Optional[SessionType] = SessionType.AGENT
    input: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """DTO for updating a session."""
    status: Optional[SessionStatus] = None
    output: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[Decimal] = None
    duration_ms: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class SessionQuery(BaseModel):
    """DTO for querying sessions."""
    agent_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    parent_session_id: Optional[UUID] = None
    meta_session_id: Optional[UUID] = None
    session_type: Optional[SessionType] = None
    status: Optional[SessionStatus] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


class Session(BaseModel):
    """Session DTO."""
    id: UUID
    project_id: UUID
    agent_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    parent_session_id: Optional[UUID] = None
    meta_session_id: Optional[UUID] = None
    session_type: str
    status: str
    input: Optional[str] = None
    output: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost: Decimal = Decimal("0")
    duration_ms: int = 0
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Session Message DTOs
# -----------------------------------------------------------------------------

class SessionMessageCreate(BaseModel):
    """DTO for creating a session message."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    message_meta: Optional[Dict[str, Any]] = None


class SessionMessage(BaseModel):
    """Session message DTO."""
    id: UUID
    project_id: UUID
    session_id: UUID
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    message_meta: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    """API request for creating a session."""
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_session_id: Optional[str] = None
    meta_session_id: Optional[str] = None
    session_type: Optional[str] = "agent"
    input: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """API response for a session."""
    id: str
    project_id: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_session_id: Optional[str] = None
    meta_session_id: Optional[str] = None
    session_type: str
    status: str
    input: Optional[str] = None
    output: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    meta: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: Session) -> "SessionResponse":
        return cls(
            id=str(dto.id),
            project_id=str(dto.project_id),
            agent_id=str(dto.agent_id) if dto.agent_id else None,
            workflow_id=str(dto.workflow_id) if dto.workflow_id else None,
            parent_session_id=str(dto.parent_session_id) if dto.parent_session_id else None,
            meta_session_id=str(dto.meta_session_id) if dto.meta_session_id else None,
            session_type=dto.session_type,
            status=dto.status,
            input=dto.input,
            output=dto.output,
            tokens_input=dto.tokens_input,
            tokens_output=dto.tokens_output,
            cost=float(dto.cost),
            duration_ms=dto.duration_ms,
            meta=dto.meta,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )


class SessionsListResponse(BaseModel):
    """API response for listing sessions."""
    sessions: List[SessionResponse]
    total: int
    offset: int
    limit: int


class SessionMessageResponse(BaseModel):
    """API response for a session message."""
    id: str
    session_id: str
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: str

    @classmethod
    def from_dto(cls, dto: SessionMessage) -> "SessionMessageResponse":
        return cls(
            id=str(dto.id),
            session_id=str(dto.session_id),
            role=dto.role,
            content=dto.content,
            tool_calls=dto.tool_calls,
            created_at=dto.created_at.isoformat(),
        )


class SessionMessageCreateRequest(BaseModel):
    """API request for creating a session message."""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
