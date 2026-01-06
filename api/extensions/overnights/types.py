"""
Agent Matrix - Overnight Runs Types

Pydantic models for overnight run operations.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class OvernightRunStatus(str, Enum):
    """Overnight run status."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowResult(BaseModel):
    """Result of a single workflow execution."""
    workflow_id: UUID
    status: str  # completed, failed, skipped
    output: Optional[str] = None
    error: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0
    duration_ms: int = 0


class OvernightRunConfig(BaseModel):
    """Configuration for overnight run execution."""
    parallel: bool = False  # Run workflows in parallel
    retry_failed: bool = False  # Retry failed workflows
    max_retries: int = 3
    notify_on_complete: bool = True
    notify_emails: Optional[list[str]] = None


class OvernightRunCreate(BaseModel):
    """Create an overnight run."""
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_ids: list[UUID]
    scheduled_for: Optional[datetime] = None
    config: Optional[OvernightRunConfig] = None
    tags: Optional[list[str]] = None


class OvernightRunUpdate(BaseModel):
    """Update an overnight run."""
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_ids: Optional[list[UUID]] = None
    scheduled_for: Optional[datetime] = None
    config: Optional[OvernightRunConfig] = None
    tags: Optional[list[str]] = None


class OvernightRun(BaseModel):
    """Overnight run response."""
    id: UUID
    project_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_ids: list[UUID] = Field(default_factory=list)
    status: OvernightRunStatus
    current_workflow_index: int = 0
    workflow_results: list[WorkflowResult] = Field(default_factory=list)
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost: float = 0.0
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Optional[OvernightRunConfig] = None
    tags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class OvernightRunProgress(BaseModel):
    """Progress information for an overnight run."""
    id: UUID
    status: OvernightRunStatus
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    current_workflow_index: int
    current_workflow_id: Optional[UUID] = None
    progress_percent: float
    estimated_remaining_ms: Optional[int] = None
