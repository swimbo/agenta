"""
Agent Matrix - Overnight Runs Database Entities

Batch execution of workflows scheduled to run overnight.
"""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Enum,
    TIMESTAMP,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    Index,
)

from oss.src.dbs.postgres.shared.base import Base
from oss.src.dbs.postgres.shared.dbas import (
    ProjectScopeDBA,
    LifecycleDBA,
    IdentifierDBA,
    TagsDBA,
    MetaDBA,
)


class OvernightRunDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, TagsDBA, MetaDBA):
    """
    Overnight run entity.

    Schedules and tracks batch execution of multiple workflows.
    """
    __tablename__ = "am_overnight_runs"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_overnight_runs_project_id_status", "project_id", "status"),
        Index("ix_am_overnight_runs_project_id_scheduled_for", "project_id", "scheduled_for"),
    )

    # Basic info
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Workflows to execute (list of workflow IDs)
    workflow_ids = Column(JSONB(none_as_null=True), default=[])

    # Status
    status = Column(
        Enum(
            "scheduled", "running", "paused", "completed", "failed", "cancelled",
            name="am_overnight_run_status"
        ),
        default="scheduled",
        nullable=False,
    )

    # Progress tracking
    current_workflow_index = Column(Integer, default=0)
    workflow_results = Column(JSONB(none_as_null=True), default=[])  # [{workflow_id, status, output, cost, duration_ms}]

    # Cost tracking
    total_tokens_input = Column(Integer, default=0)
    total_tokens_output = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0)

    # Timing
    scheduled_for = Column(TIMESTAMP(timezone=True), nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Configuration
    config = Column(JSONB(none_as_null=True), nullable=True)  # {parallel, retry_failed, notify_on_complete}
