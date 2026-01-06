"""Agent Matrix Extensions

Revision ID: am001
Revises: fd77265d65dc
Create Date: 2025-12-31 00:00:00.000000

Adds Agent Matrix custom entities:
- agents (with versions, rules, skills)
- workflows (with executions, costs)
- sessions (with messages)
- interventions
- gates
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "am001"
down_revision: Union[str, None] = "7a3d1c4f5b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # AGENTS
    # ==========================================================================

    op.create_table(
        "am_agents",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        # Core fields
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        # Model configuration
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("temperature", sa.Float(), server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        # Tools configuration
        sa.Column("tools", postgresql.JSONB(none_as_null=True), server_default="[]"),
        # Scope and visibility
        sa.Column(
            "scope",
            sa.Enum("personal", "team", "public", name="am_agent_scope"),
            server_default="personal",
            nullable=False,
        ),
        sa.Column("is_public", sa.Boolean(), server_default="false"),
        # Versioning and branching
        sa.Column(
            "branch",
            sa.Enum("dev", "staging", "prod", name="am_agent_branch"),
            server_default="dev",
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1"),
        # Forking support
        sa.Column("forked_from", sa.UUID(), nullable=True),
        # TagsDBA
        sa.Column("tags", postgresql.JSONB(none_as_null=True), nullable=True),
        # MetaDBA
        sa.Column("meta", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("flags", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "forked_from"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_am_agents_project_id_name", "am_agents", ["project_id", "name"])
    op.create_index("ix_am_agents_project_id_scope", "am_agents", ["project_id", "scope"])
    op.create_index("ix_am_agents_project_id_branch", "am_agents", ["project_id", "branch"])
    op.create_index("ix_am_agents_project_id_is_public", "am_agents", ["project_id", "is_public"])

    # --------------------------------------------------------------------------
    # AGENT VERSIONS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_agent_versions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        # Snapshot of agent config
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("tools", postgresql.JSONB(none_as_null=True), nullable=True),
        # Version metadata
        sa.Column("changelog", sa.Text(), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_agent_versions_project_agent", "am_agent_versions", ["project_id", "agent_id"])
    op.create_index("ix_am_agent_versions_project_version", "am_agent_versions", ["project_id", "version"])

    # --------------------------------------------------------------------------
    # AGENT RULES
    # --------------------------------------------------------------------------

    op.create_table(
        "am_agent_rules",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        # Rule definition
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("condition", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("action", postgresql.JSONB(none_as_null=True), nullable=True),
        # Priority and state
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_agent_rules_project_agent", "am_agent_rules", ["project_id", "agent_id"])
    op.create_index("ix_am_agent_rules_project_active", "am_agent_rules", ["project_id", "is_active"])

    # --------------------------------------------------------------------------
    # AGENT SKILLS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_agent_skills",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0"),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_agent_skills_project_agent", "am_agent_skills", ["project_id", "agent_id"])

    # --------------------------------------------------------------------------
    # RULE EXECUTIONS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_rule_executions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rule_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=True),
        # Execution result
        sa.Column(
            "status",
            sa.Enum("triggered", "skipped", "failed", name="am_rule_execution_status"),
            nullable=False,
        ),
        sa.Column("result", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "rule_id"],
            ["am_agent_rules.project_id", "am_agent_rules.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_rule_executions_project_rule", "am_rule_executions", ["project_id", "rule_id"])
    op.create_index("ix_am_rule_executions_project_session", "am_rule_executions", ["project_id", "session_id"])

    # ==========================================================================
    # WORKFLOWS
    # ==========================================================================

    op.create_table(
        "am_workflows",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Steps configuration
        sa.Column("steps", postgresql.JSONB(none_as_null=True), server_default="[]"),
        # Scope and environment
        sa.Column(
            "scope",
            sa.Enum("personal", "team", "public", name="am_workflow_scope"),
            server_default="personal",
            nullable=False,
        ),
        sa.Column(
            "environment",
            sa.Enum("dev", "staging", "prod", name="am_workflow_environment"),
            server_default="dev",
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1"),
        # TagsDBA
        sa.Column("tags", postgresql.JSONB(none_as_null=True), nullable=True),
        # MetaDBA
        sa.Column("meta", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("flags", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_am_workflows_project_name", "am_workflows", ["project_id", "name"])
    op.create_index("ix_am_workflows_project_scope", "am_workflows", ["project_id", "scope"])

    # --------------------------------------------------------------------------
    # WORKFLOW EXECUTIONS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_workflow_executions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        # Execution state
        sa.Column(
            "status",
            sa.Enum(
                "pending", "running", "paused", "completed", "failed", "cancelled",
                name="am_workflow_execution_status"
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("current_step_id", sa.String(100), nullable=True),
        sa.Column("step_results", postgresql.JSONB(none_as_null=True), server_default="{}"),
        # Input/output
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        # Timing
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_workflow_executions_project_workflow", "am_workflow_executions", ["project_id", "workflow_id"])
    op.create_index("ix_am_workflow_executions_project_status", "am_workflow_executions", ["project_id", "status"])

    # --------------------------------------------------------------------------
    # WORKFLOW COSTS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_workflow_costs",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(100), nullable=False),
        # Cost details
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("tokens_input", sa.Integer(), server_default="0"),
        sa.Column("tokens_output", sa.Integer(), server_default="0"),
        sa.Column("cost", sa.Numeric(10, 6), server_default="0"),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "execution_id"],
            ["am_workflow_executions.project_id", "am_workflow_executions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_workflow_costs_project_execution", "am_workflow_costs", ["project_id", "execution_id"])

    # ==========================================================================
    # SESSIONS
    # ==========================================================================

    op.create_table(
        "am_sessions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        # Associations
        sa.Column("agent_id", sa.UUID(), nullable=True),
        sa.Column("workflow_id", sa.UUID(), nullable=True),
        sa.Column("parent_session_id", sa.UUID(), nullable=True),
        sa.Column("meta_session_id", sa.UUID(), nullable=True),
        # Session type and status
        sa.Column(
            "session_type",
            sa.Enum(
                "agent", "workflow", "overnight", "prompts", "test", "interactive",
                name="am_session_type"
            ),
            server_default="agent",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "running", "completed", "failed", "cancelled",
                name="am_session_status"
            ),
            server_default="pending",
            nullable=False,
        ),
        # Input/output
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        # Metrics
        sa.Column("tokens_input", sa.Integer(), server_default="0"),
        sa.Column("tokens_output", sa.Integer(), server_default="0"),
        sa.Column("cost", sa.Numeric(10, 6), server_default="0"),
        sa.Column("duration_ms", sa.Integer(), server_default="0"),
        # MetaDBA
        sa.Column("meta", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("flags", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "parent_session_id"],
            ["am_sessions.project_id", "am_sessions.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_am_sessions_project_agent", "am_sessions", ["project_id", "agent_id"])
    op.create_index("ix_am_sessions_project_workflow", "am_sessions", ["project_id", "workflow_id"])
    op.create_index("ix_am_sessions_project_status", "am_sessions", ["project_id", "status"])
    op.create_index("ix_am_sessions_project_type", "am_sessions", ["project_id", "session_type"])

    # --------------------------------------------------------------------------
    # SESSION MESSAGES
    # --------------------------------------------------------------------------

    op.create_table(
        "am_session_messages",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        # Message content
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", "tool", name="am_message_role"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("message_meta", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["am_sessions.project_id", "am_sessions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_session_messages_project_session", "am_session_messages", ["project_id", "session_id"])

    # ==========================================================================
    # INTERVENTIONS
    # ==========================================================================

    op.create_table(
        "am_interventions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(100), nullable=True),
        # Intervention type
        sa.Column(
            "intervention_type",
            sa.Enum(
                "pause", "resume", "inject", "approve", "reject", "cancel",
                name="am_intervention_type"
            ),
            nullable=False,
        ),
        # Intervention content
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(none_as_null=True), nullable=True),
        # Status tracking
        sa.Column(
            "status",
            sa.Enum("pending", "applied", "failed", name="am_intervention_status"),
            server_default="pending",
            nullable=False,
        ),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "execution_id"],
            ["am_workflow_executions.project_id", "am_workflow_executions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_interventions_project_workflow", "am_interventions", ["project_id", "workflow_id"])
    op.create_index("ix_am_interventions_project_execution", "am_interventions", ["project_id", "execution_id"])
    op.create_index("ix_am_interventions_project_type", "am_interventions", ["project_id", "intervention_type"])

    # ==========================================================================
    # GATES
    # ==========================================================================

    op.create_table(
        "am_gates",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(100), nullable=False),
        # Gate type
        sa.Column(
            "gate_type",
            sa.Enum("approval", "review", "deploy", "cost", name="am_gate_type"),
            nullable=False,
        ),
        # Gate status
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="am_gate_status"),
            server_default="pending",
            nullable=False,
        ),
        # Review details
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        # Gate configuration and context
        sa.Column("config", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("context", postgresql.JSONB(none_as_null=True), nullable=True),
        # LifecycleDBA
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_id", sa.UUID(), nullable=True),
        sa.Column("deleted_by_id", sa.UUID(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "workflow_id"],
            ["am_workflows.project_id", "am_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "execution_id"],
            ["am_workflow_executions.project_id", "am_workflow_executions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_gates_project_workflow", "am_gates", ["project_id", "workflow_id"])
    op.create_index("ix_am_gates_project_execution", "am_gates", ["project_id", "execution_id"])
    op.create_index("ix_am_gates_project_status", "am_gates", ["project_id", "status"])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting FKs)
    op.drop_table("am_gates")
    op.drop_table("am_interventions")
    op.drop_table("am_session_messages")
    op.drop_table("am_sessions")
    op.drop_table("am_workflow_costs")
    op.drop_table("am_workflow_executions")
    op.drop_table("am_workflows")
    op.drop_table("am_rule_executions")
    op.drop_table("am_agent_skills")
    op.drop_table("am_agent_rules")
    op.drop_table("am_agent_versions")
    op.drop_table("am_agents")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS am_gate_status")
    op.execute("DROP TYPE IF EXISTS am_gate_type")
    op.execute("DROP TYPE IF EXISTS am_intervention_status")
    op.execute("DROP TYPE IF EXISTS am_intervention_type")
    op.execute("DROP TYPE IF EXISTS am_message_role")
    op.execute("DROP TYPE IF EXISTS am_session_status")
    op.execute("DROP TYPE IF EXISTS am_session_type")
    op.execute("DROP TYPE IF EXISTS am_workflow_execution_status")
    op.execute("DROP TYPE IF EXISTS am_workflow_environment")
    op.execute("DROP TYPE IF EXISTS am_workflow_scope")
    op.execute("DROP TYPE IF EXISTS am_rule_execution_status")
    op.execute("DROP TYPE IF EXISTS am_agent_branch")
    op.execute("DROP TYPE IF EXISTS am_agent_scope")
