"""
Agent Matrix - Interventions Types

Pydantic models for intervention DTOs and request/response types.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class InterventionType(str, Enum):
    PAUSE = "pause"
    RESUME = "resume"
    INJECT = "inject"
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"


class InterventionStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"


# -----------------------------------------------------------------------------
# Intervention DTOs
# -----------------------------------------------------------------------------

class InterventionCreate(BaseModel):
    """DTO for creating an intervention."""
    workflow_id: UUID
    execution_id: UUID
    step_id: Optional[str] = None
    intervention_type: InterventionType
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class InterventionQuery(BaseModel):
    """DTO for querying interventions."""
    workflow_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    intervention_type: Optional[InterventionType] = None
    status: Optional[InterventionStatus] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


class Intervention(BaseModel):
    """Intervention DTO."""
    id: UUID
    project_id: UUID
    workflow_id: UUID
    execution_id: UUID
    step_id: Optional[str] = None
    intervention_type: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class InterventionCreateRequest(BaseModel):
    """API request for creating an intervention."""
    workflow_id: str
    execution_id: str
    step_id: Optional[str] = None
    intervention_type: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class InterventionResponse(BaseModel):
    """API response for an intervention."""
    id: str
    workflow_id: str
    execution_id: str
    step_id: Optional[str] = None
    intervention_type: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: Intervention) -> "InterventionResponse":
        return cls(
            id=str(dto.id),
            workflow_id=str(dto.workflow_id),
            execution_id=str(dto.execution_id),
            step_id=dto.step_id,
            intervention_type=dto.intervention_type,
            message=dto.message,
            data=dto.data,
            status=dto.status,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )


class InterventionsListResponse(BaseModel):
    """API response for listing interventions."""
    interventions: List[InterventionResponse]
    total: int
    offset: int
    limit: int


# Convenience request types for specific interventions
class PauseRequest(BaseModel):
    """Request to pause a workflow execution."""
    message: Optional[str] = None


class ResumeRequest(BaseModel):
    """Request to resume a paused execution."""
    message: Optional[str] = None


class InjectRequest(BaseModel):
    """Request to inject data into an execution."""
    message: Optional[str] = None
    data: Dict[str, Any]
    step_id: Optional[str] = None


class ApproveRequest(BaseModel):
    """Request to approve a gate or step."""
    message: Optional[str] = None
    step_id: Optional[str] = None


class RejectRequest(BaseModel):
    """Request to reject a gate or step."""
    message: Optional[str] = None
    reason: str
    step_id: Optional[str] = None
