"""
Agent Matrix - Gates Database Entities

Approval gates for workflow steps: approval, review, deploy, cost gates.
"""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Text,
    Enum,
    UUID,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    Index,
)

from oss.src.dbs.postgres.shared.base import Base
from oss.src.dbs.postgres.shared.dbas import (
    ProjectScopeDBA,
    LifecycleDBA,
    IdentifierDBA,
)


class GateDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Gate entity.

    Defines approval gates that block workflow progression until reviewed.
    """
    __tablename__ = "am_gates"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "execution_id"],
            ["am_workflow_executions.project_id", "am_workflow_executions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_gates_project_id_workflow_id", "project_id", "workflow_id"),
        Index("ix_am_gates_project_id_execution_id", "project_id", "execution_id"),
        Index("ix_am_gates_project_id_status", "project_id", "status"),
    )

    workflow_id = Column(UUID(as_uuid=True), nullable=False)
    execution_id = Column(UUID(as_uuid=True), nullable=False)
    step_id = Column(String(100), nullable=False)

    # Gate type
    gate_type = Column(
        Enum("approval", "review", "deploy", "cost", name="gate_type"),
        nullable=False,
    )

    # Gate status
    status = Column(
        Enum("pending", "approved", "rejected", name="gate_status"),
        default="pending",
        nullable=False,
    )

    # Review details
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Gate configuration and context
    config = Column(JSONB(none_as_null=True), nullable=True)
    context = Column(JSONB(none_as_null=True), nullable=True)
