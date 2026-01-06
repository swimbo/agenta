"""
Agent Matrix - Workflows Database Entities

Multi-step workflow orchestration with execution tracking.
"""

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Enum,
    UUID,
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


CASCADE_ALL_DELETE = "all, delete-orphan"


class WorkflowDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, TagsDBA, MetaDBA):
    """
    Workflow definition entity.

    Stores multi-step workflow configurations with step dependencies.
    """
    __tablename__ = "am_workflows"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_workflows_project_id_name", "project_id", "name"),
        Index("ix_am_workflows_project_id_scope", "project_id", "scope"),
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Steps configuration: [{id, name, agent_id, depends_on, config}]
    steps = Column(JSONB(none_as_null=True), default=[])

    # Scope and environment
    scope = Column(
        Enum("personal", "team", "public", name="workflow_scope"),
        default="personal",
        nullable=False,
    )
    environment = Column(
        Enum("dev", "staging", "prod", name="workflow_environment"),
        default="dev",
        nullable=False,
    )
    version = Column(Integer, default=1)

    # Relationships
    executions = relationship(
        "WorkflowExecutionDBE",
        back_populates="workflow",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
    )


class WorkflowExecutionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Workflow execution instance.

    Tracks the execution state of a workflow run.
    """
    __tablename__ = "am_workflow_executions"

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
        Index("ix_am_workflow_executions_project_id_workflow_id", "project_id", "workflow_id"),
        Index("ix_am_workflow_executions_project_id_status", "project_id", "status"),
    )

    workflow_id = Column(UUID(as_uuid=True), nullable=False)

    # Execution state
    status = Column(
        Enum("pending", "running", "paused", "completed", "failed", "cancelled",
             name="workflow_execution_status"),
        default="pending",
        nullable=False,
    )
    current_step_id = Column(String(100), nullable=True)

    # Step results: {step_id: {status, output, cost, duration_ms}}
    step_results = Column(JSONB(none_as_null=True), default={})

    # Input/output
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)

    # Timing
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationship
    workflow = relationship("WorkflowDBE", back_populates="executions")
    costs = relationship(
        "WorkflowCostDBE",
        back_populates="execution",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
    )


class WorkflowCostDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Workflow execution cost tracking per step.
    """
    __tablename__ = "am_workflow_costs"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "execution_id"],
            ["am_workflow_executions.project_id", "am_workflow_executions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_workflow_costs_project_id_execution_id", "project_id", "execution_id"),
    )

    workflow_id = Column(UUID(as_uuid=True), nullable=False)
    execution_id = Column(UUID(as_uuid=True), nullable=False)
    step_id = Column(String(100), nullable=False)

    # Cost details
    model = Column(String(100), nullable=True)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Numeric(10, 6), default=0)

    # Relationship
    execution = relationship("WorkflowExecutionDBE", back_populates="costs")
