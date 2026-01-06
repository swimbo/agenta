"""
Agent Matrix - Interventions Database Entities

Human-in-the-loop workflow controls: pause, resume, inject, approve, reject.
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


class InterventionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Intervention entity.

    Records human interventions in workflow execution.
    """
    __tablename__ = "am_interventions"

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
        Index("ix_am_interventions_project_id_workflow_id", "project_id", "workflow_id"),
        Index("ix_am_interventions_project_id_execution_id", "project_id", "execution_id"),
        Index("ix_am_interventions_project_id_type", "project_id", "intervention_type"),
    )

    workflow_id = Column(UUID(as_uuid=True), nullable=False)
    execution_id = Column(UUID(as_uuid=True), nullable=False)
    step_id = Column(String(100), nullable=True)

    # Intervention type
    intervention_type = Column(
        Enum("pause", "resume", "inject", "approve", "reject", "cancel",
             name="intervention_type"),
        nullable=False,
    )

    # Intervention content
    message = Column(Text, nullable=True)
    data = Column(JSONB(none_as_null=True), nullable=True)

    # Status tracking
    status = Column(
        Enum("pending", "applied", "failed", name="intervention_status"),
        default="pending",
        nullable=False,
    )
