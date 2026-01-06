"""
Agent Matrix - Meta Sessions Database Entities

Meta sessions group related sessions (plan, build, monitor phases).
Monitoring sessions track guardrails and testing agents.
"""

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Boolean,
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
    MetaDBA,
)


CASCADE_ALL_DELETE = "all, delete-orphan"


class MetaSessionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, MetaDBA):
    """
    Meta session entity.

    Groups related sessions under a common context (plan/build/monitor phases).
    """
    __tablename__ = "am_meta_sessions"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_meta_sessions_project_id_type", "project_id", "meta_type"),
        Index("ix_am_meta_sessions_project_id_status", "project_id", "status"),
    )

    # Meta session type
    meta_type = Column(
        Enum("plan", "build", "monitor", name="am_meta_session_type"),
        nullable=False,
    )

    # Status
    status = Column(
        Enum("active", "stopped", name="am_meta_session_status"),
        default="active",
        nullable=False,
    )

    # Optional name/description
    name = Column(String(255), nullable=True)
    description = Column(String(1024), nullable=True)

    # Configuration
    config = Column(JSONB(none_as_null=True), nullable=True)

    # Relationships
    monitoring_sessions = relationship(
        "MonitoringSessionDBE",
        back_populates="target_meta_session",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
    )


class MonitoringSessionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Monitoring session entity.

    Tracks agents that monitor other sessions (guardrails, testing).
    """
    __tablename__ = "am_monitoring_sessions"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "target_meta_session_id"],
            ["am_meta_sessions.project_id", "am_meta_sessions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_monitoring_sessions_project_target", "project_id", "target_meta_session_id"),
        Index("ix_am_monitoring_sessions_project_type", "project_id", "monitoring_type"),
    )

    # What we're monitoring
    target_meta_session_id = Column(UUID(as_uuid=True), nullable=False)

    # Type of monitoring
    monitoring_type = Column(
        Enum("guardrails", "testing", name="am_monitoring_type"),
        nullable=False,
    )

    # Agent doing the monitoring
    agent_id = Column(UUID(as_uuid=True), nullable=False)

    # Whether this was auto-started
    auto_started = Column(Boolean, default=False)

    # Status
    status = Column(
        Enum("pending", "running", "completed", "failed", name="am_monitoring_session_status"),
        default="pending",
        nullable=False,
    )

    # Results
    results = Column(JSONB(none_as_null=True), nullable=True)

    # Relationship
    target_meta_session = relationship("MetaSessionDBE", back_populates="monitoring_sessions")
