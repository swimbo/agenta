"""
Agent Matrix - Meta Sessions Types

Pydantic models for meta session operations.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class MetaSessionType(str, Enum):
    """Meta session types."""
    PLAN = "plan"
    BUILD = "build"
    MONITOR = "monitor"


class MetaSessionStatus(str, Enum):
    """Meta session status."""
    ACTIVE = "active"
    STOPPED = "stopped"


class MonitoringType(str, Enum):
    """Monitoring session types."""
    GUARDRAILS = "guardrails"
    TESTING = "testing"


class MonitoringSessionStatus(str, Enum):
    """Monitoring session status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# DTOs

class MetaSessionCreate(BaseModel):
    """Create a meta session."""
    meta_type: MetaSessionType
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    auto_start_guardrails: bool = Field(default=False)


class MetaSessionUpdate(BaseModel):
    """Update a meta session."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MetaSessionStatus] = None
    config: Optional[dict[str, Any]] = None


class MetaSession(BaseModel):
    """Meta session response."""
    id: UUID
    project_id: UUID
    meta_type: MetaSessionType
    status: MetaSessionStatus
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class MonitoringSessionCreate(BaseModel):
    """Create a monitoring session."""
    target_meta_session_id: UUID
    monitoring_type: MonitoringType
    agent_id: UUID
    auto_started: bool = False


class MonitoringSessionUpdate(BaseModel):
    """Update a monitoring session."""
    status: Optional[MonitoringSessionStatus] = None
    results: Optional[dict[str, Any]] = None


class MonitoringSession(BaseModel):
    """Monitoring session response."""
    id: UUID
    project_id: UUID
    target_meta_session_id: UUID
    monitoring_type: MonitoringType
    agent_id: UUID
    auto_started: bool
    status: MonitoringSessionStatus
    results: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetaSessionWithMonitoring(MetaSession):
    """Meta session with associated monitoring sessions."""
    monitoring_sessions: list[MonitoringSession] = Field(default_factory=list)
