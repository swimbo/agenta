"""
Agent Matrix - Gates Types

Pydantic models for gate DTOs and request/response types.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class GateType(str, Enum):
    APPROVAL = "approval"
    REVIEW = "review"
    DEPLOY = "deploy"
    COST = "cost"


class GateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# -----------------------------------------------------------------------------
# Gate DTOs
# -----------------------------------------------------------------------------

class GateCreate(BaseModel):
    """DTO for creating a gate."""
    workflow_id: UUID
    execution_id: UUID
    step_id: str
    gate_type: GateType
    config: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class GateQuery(BaseModel):
    """DTO for querying gates."""
    workflow_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    gate_type: Optional[GateType] = None
    status: Optional[GateStatus] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


class Gate(BaseModel):
    """Gate DTO."""
    id: UUID
    project_id: UUID
    workflow_id: UUID
    execution_id: UUID
    step_id: str
    gate_type: str
    status: str
    reviewed_by: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class GateCreateRequest(BaseModel):
    """API request for creating a gate."""
    workflow_id: str
    execution_id: str
    step_id: str
    gate_type: str
    config: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class GateResponse(BaseModel):
    """API response for a gate."""
    id: str
    workflow_id: str
    execution_id: str
    step_id: str
    gate_type: str
    status: str
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: Gate) -> "GateResponse":
        return cls(
            id=str(dto.id),
            workflow_id=str(dto.workflow_id),
            execution_id=str(dto.execution_id),
            step_id=dto.step_id,
            gate_type=dto.gate_type,
            status=dto.status,
            reviewed_by=str(dto.reviewed_by) if dto.reviewed_by else None,
            rejection_reason=dto.rejection_reason,
            config=dto.config,
            context=dto.context,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )


class GatesListResponse(BaseModel):
    """API response for listing gates."""
    gates: List[GateResponse]
    total: int
    offset: int
    limit: int


class GateApproveRequest(BaseModel):
    """Request to approve a gate."""
    message: Optional[str] = None


class GateRejectRequest(BaseModel):
    """Request to reject a gate."""
    reason: str
