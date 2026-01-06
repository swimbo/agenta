"""
Agent Matrix - Workflows Types

Pydantic models for workflow DTOs and request/response types.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class WorkflowScope(str, Enum):
    PERSONAL = "personal"
    TEAM = "team"
    PUBLIC = "public"


class WorkflowEnvironment(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class WorkflowExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# -----------------------------------------------------------------------------
# Workflow Step DTOs
# -----------------------------------------------------------------------------

class WorkflowStep(BaseModel):
    """Workflow step configuration."""
    id: str
    name: str
    agent_id: Optional[UUID] = None
    depends_on: List[str] = []
    config: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Workflow DTOs
# -----------------------------------------------------------------------------

class WorkflowCreate(BaseModel):
    """DTO for creating a workflow."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[WorkflowStep] = []
    scope: Optional[WorkflowScope] = WorkflowScope.PERSONAL
    environment: Optional[WorkflowEnvironment] = WorkflowEnvironment.DEV
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class WorkflowUpdate(BaseModel):
    """DTO for updating a workflow."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    scope: Optional[WorkflowScope] = None
    environment: Optional[WorkflowEnvironment] = None
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class WorkflowQuery(BaseModel):
    """DTO for querying workflows."""
    name: Optional[str] = None
    scope: Optional[WorkflowScope] = None
    environment: Optional[WorkflowEnvironment] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


class Workflow(BaseModel):
    """Workflow DTO."""
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    scope: str
    environment: str
    version: int
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Workflow Execution DTOs
# -----------------------------------------------------------------------------

class WorkflowExecutionCreate(BaseModel):
    """DTO for creating a workflow execution."""
    input: Optional[str] = None


class WorkflowExecution(BaseModel):
    """Workflow execution DTO."""
    id: UUID
    project_id: UUID
    workflow_id: UUID
    status: str
    current_step_id: Optional[str] = None
    step_results: Dict[str, Any] = {}
    input: Optional[str] = None
    output: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowExecutionQuery(BaseModel):
    """DTO for querying workflow executions."""
    workflow_id: Optional[UUID] = None
    status: Optional[WorkflowExecutionStatus] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class WorkflowCreateRequest(BaseModel):
    """API request for creating a workflow."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    scope: Optional[str] = "personal"
    environment: Optional[str] = "dev"
    tags: Optional[Dict[str, Any]] = None


class WorkflowUpdateRequest(BaseModel):
    """API request for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    scope: Optional[str] = None
    environment: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """API response for a workflow."""
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    scope: str
    environment: str
    version: int
    tags: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: Workflow) -> "WorkflowResponse":
        return cls(
            id=str(dto.id),
            project_id=str(dto.project_id),
            name=dto.name,
            description=dto.description,
            steps=dto.steps,
            scope=dto.scope,
            environment=dto.environment,
            version=dto.version,
            tags=dto.tags,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )


class WorkflowsListResponse(BaseModel):
    """API response for listing workflows."""
    workflows: List[WorkflowResponse]
    total: int
    offset: int
    limit: int


class WorkflowExecutionResponse(BaseModel):
    """API response for a workflow execution."""
    id: str
    workflow_id: str
    status: str
    current_step_id: Optional[str] = None
    step_results: Dict[str, Any] = {}
    input: Optional[str] = None
    output: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str

    @classmethod
    def from_dto(cls, dto: WorkflowExecution) -> "WorkflowExecutionResponse":
        return cls(
            id=str(dto.id),
            workflow_id=str(dto.workflow_id),
            status=dto.status,
            current_step_id=dto.current_step_id,
            step_results=dto.step_results,
            input=dto.input,
            output=dto.output,
            started_at=dto.started_at.isoformat() if dto.started_at else None,
            completed_at=dto.completed_at.isoformat() if dto.completed_at else None,
            created_at=dto.created_at.isoformat(),
        )


class WorkflowRunRequest(BaseModel):
    """Request to run a workflow."""
    input: Optional[str] = None
    step_overrides: Optional[Dict[str, Dict[str, Any]]] = None
