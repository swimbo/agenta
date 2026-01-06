"""
Agent Matrix - Sessions Database Entities

Agent/workflow execution sessions with message history.
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
    MetaDBA,
)


CASCADE_ALL_DELETE = "all, delete-orphan"


class SessionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, MetaDBA):
    """
    Execution session entity.

    Tracks agent or workflow execution with hierarchical session support.
    """
    __tablename__ = "am_sessions"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["project_id", "parent_session_id"],
            ["am_sessions.project_id", "am_sessions.id"],
            ondelete="SET NULL",
        ),
        Index("ix_am_sessions_project_id_agent_id", "project_id", "agent_id"),
        Index("ix_am_sessions_project_id_workflow_id", "project_id", "workflow_id"),
        Index("ix_am_sessions_project_id_status", "project_id", "status"),
        Index("ix_am_sessions_project_id_session_type", "project_id", "session_type"),
    )

    # Associations
    agent_id = Column(UUID(as_uuid=True), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), nullable=True)
    parent_session_id = Column(UUID(as_uuid=True), nullable=True)
    meta_session_id = Column(UUID(as_uuid=True), nullable=True)

    # Session type and status
    session_type = Column(
        Enum("agent", "workflow", "overnight", "prompts", "test", "interactive",
             name="session_type"),
        default="agent",
        nullable=False,
    )
    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled",
             name="session_status"),
        default="pending",
        nullable=False,
    )

    # Input/output
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)

    # Metrics
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Numeric(10, 6), default=0)
    duration_ms = Column(Integer, default=0)

    # Relationships
    messages = relationship(
        "SessionMessageDBE",
        back_populates="session",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
        order_by="SessionMessageDBE.created_at",
    )


class SessionMessageDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Session message entity.

    Stores conversation history within a session.
    """
    __tablename__ = "am_session_messages"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["am_sessions.project_id", "am_sessions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_session_messages_project_id_session_id", "project_id", "session_id"),
    )

    session_id = Column(UUID(as_uuid=True), nullable=False)

    # Message content
    role = Column(
        Enum("user", "assistant", "system", "tool", name="message_role"),
        nullable=False,
    )
    content = Column(Text, nullable=True)

    # Tool calls for assistant messages
    tool_calls = Column(JSONB(none_as_null=True), nullable=True)

    # Additional metadata
    message_meta = Column(JSONB(none_as_null=True), nullable=True)

    # Relationship
    session = relationship("SessionDBE", back_populates="messages")
