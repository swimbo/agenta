"""
Agent Matrix - Agents Database Entities

Agent configurations with versioning, branches, rules, and skills.
"""

import uuid_utils.compat as uuid

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
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
    TagsDBA,
    MetaDBA,
)


CASCADE_ALL_DELETE = "all, delete-orphan"


# Enums for agent fields
class AgentScope:
    PERSONAL = "personal"
    TEAM = "team"
    PUBLIC = "public"


class AgentBranch:
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class AgentDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, TagsDBA, MetaDBA):
    """
    Agent configuration entity.

    Stores agent definitions including system prompt, model settings,
    versioning, branching, and scope controls.
    """
    __tablename__ = "am_agents"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "forked_from"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="SET NULL",
        ),
        Index("ix_agents_project_id_name", "project_id", "name"),
        Index("ix_agents_project_id_scope", "project_id", "scope"),
        Index("ix_agents_project_id_branch", "project_id", "branch"),
        Index("ix_agents_project_id_is_public", "project_id", "is_public"),
    )

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)

    # Model configuration
    model = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, nullable=True)

    # Tools configuration (list of tool names)
    tools = Column(JSONB(none_as_null=True), default=[])

    # Scope and visibility
    scope = Column(
        Enum("personal", "team", "public", name="agent_scope"),
        default="personal",
        nullable=False,
    )
    is_public = Column(Boolean, default=False)

    # Versioning and branching
    branch = Column(
        Enum("dev", "staging", "prod", name="agent_branch"),
        default="dev",
        nullable=False,
    )
    version = Column(Integer, default=1)

    # Forking support
    forked_from = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    versions = relationship(
        "AgentVersionDBE",
        back_populates="agent",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
    )
    rules = relationship(
        "AgentRuleDBE",
        back_populates="agent",
        cascade=CASCADE_ALL_DELETE,
        passive_deletes=True,
    )


class AgentVersionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Agent version history.

    Tracks changes to agent configuration over time.
    """
    __tablename__ = "am_agent_versions"

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
            ondelete="CASCADE",
        ),
        Index("ix_am_agent_versions_project_id_agent_id", "project_id", "agent_id"),
        Index("ix_am_agent_versions_project_id_version", "project_id", "version"),
    )

    agent_id = Column(UUID(as_uuid=True), nullable=False)
    version = Column(Integer, nullable=False)

    # Snapshot of agent config at this version
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    tools = Column(JSONB(none_as_null=True), nullable=True)

    # Version metadata
    changelog = Column(Text, nullable=True)

    # Relationship
    agent = relationship("AgentDBE", back_populates="versions")


class AgentRuleDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Agent rule entity.

    Defines conditional behaviors and actions for agents.
    """
    __tablename__ = "am_agent_rules"

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
            ondelete="CASCADE",
        ),
        Index("ix_am_agent_rules_project_id_agent_id", "project_id", "agent_id"),
        Index("ix_am_agent_rules_project_id_is_active", "project_id", "is_active"),
    )

    agent_id = Column(UUID(as_uuid=True), nullable=False)

    # Rule definition
    name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # e.g., "trigger", "guard", "transform"

    # Condition and action as JSON
    condition = Column(JSONB(none_as_null=True), nullable=True)
    action = Column(JSONB(none_as_null=True), nullable=True)

    # Priority and state
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationship
    agent = relationship("AgentDBE", back_populates="rules")


class AgentSkillDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Agent-Skill association.

    Links agents to reusable skills.
    """
    __tablename__ = "am_agent_skills"

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
            ondelete="CASCADE",
        ),
        Index("ix_am_agent_skills_project_id_agent_id", "project_id", "agent_id"),
    )

    agent_id = Column(UUID(as_uuid=True), nullable=False)
    skill_id = Column(UUID(as_uuid=True), nullable=False)
    priority = Column(Integer, default=0)


class RuleExecutionDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA):
    """
    Rule execution history.

    Tracks when rules are triggered during agent execution.
    """
    __tablename__ = "am_rule_executions"

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["project_id", "rule_id"],
            ["am_agent_rules.project_id", "am_agent_rules.id"],
            ondelete="CASCADE",
        ),
        Index("ix_am_rule_executions_project_id_rule_id", "project_id", "rule_id"),
        Index("ix_am_rule_executions_project_id_session_id", "project_id", "session_id"),
    )

    rule_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=True)

    # Execution result
    status = Column(
        Enum("triggered", "skipped", "failed", name="rule_execution_status"),
        nullable=False,
    )
    result = Column(JSONB(none_as_null=True), nullable=True)
