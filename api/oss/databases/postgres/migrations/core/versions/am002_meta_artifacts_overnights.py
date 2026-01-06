"""Agent Matrix Extensions - Phase 3 & 4

Revision ID: am002
Revises: am001
Create Date: 2025-12-31 00:30:00.000000

Adds:
- Meta Sessions & Monitoring Sessions
- Artifacts with versioning
- Overnight Runs batch execution
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "am002"
down_revision: Union[str, None] = "am001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # META SESSIONS
    # ==========================================================================

    op.create_table(
        "am_meta_sessions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        # Meta session type
        sa.Column(
            "meta_type",
            sa.Enum("plan", "build", "monitor", name="am_meta_session_type"),
            nullable=False,
        ),
        # Status
        sa.Column(
            "status",
            sa.Enum("active", "stopped", name="am_meta_session_status"),
            server_default="active",
            nullable=False,
        ),
        # Info
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("config", postgresql.JSONB(none_as_null=True), nullable=True),
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
    op.create_index("ix_am_meta_sessions_project_type", "am_meta_sessions", ["project_id", "meta_type"])
    op.create_index("ix_am_meta_sessions_project_status", "am_meta_sessions", ["project_id", "status"])

    # --------------------------------------------------------------------------
    # MONITORING SESSIONS
    # --------------------------------------------------------------------------

    op.create_table(
        "am_monitoring_sessions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("target_meta_session_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        # Type
        sa.Column(
            "monitoring_type",
            sa.Enum("guardrails", "testing", name="am_monitoring_type"),
            nullable=False,
        ),
        sa.Column("auto_started", sa.Boolean(), server_default="false"),
        # Status
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="am_monitoring_session_status"),
            server_default="pending",
            nullable=False,
        ),
        # Results
        sa.Column("results", postgresql.JSONB(none_as_null=True), nullable=True),
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
            ["project_id", "target_meta_session_id"],
            ["am_meta_sessions.project_id", "am_meta_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "agent_id"],
            ["am_agents.project_id", "am_agents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_am_monitoring_sessions_project_target", "am_monitoring_sessions", ["project_id", "target_meta_session_id"])
    op.create_index("ix_am_monitoring_sessions_project_type", "am_monitoring_sessions", ["project_id", "monitoring_type"])

    # ==========================================================================
    # OVERNIGHT RUNS (create before artifacts due to FK)
    # ==========================================================================

    op.create_table(
        "am_overnight_runs",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        # Basic info
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        # Workflow list
        sa.Column("workflow_ids", postgresql.JSONB(none_as_null=True), server_default="[]"),
        # Status
        sa.Column(
            "status",
            sa.Enum(
                "scheduled", "running", "paused", "completed", "failed", "cancelled",
                name="am_overnight_run_status"
            ),
            server_default="scheduled",
            nullable=False,
        ),
        # Progress
        sa.Column("current_workflow_index", sa.Integer(), server_default="0"),
        sa.Column("workflow_results", postgresql.JSONB(none_as_null=True), server_default="[]"),
        # Cost tracking
        sa.Column("total_tokens_input", sa.Integer(), server_default="0"),
        sa.Column("total_tokens_output", sa.Integer(), server_default="0"),
        sa.Column("total_cost", sa.Numeric(10, 6), server_default="0"),
        # Timing
        sa.Column("scheduled_for", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Configuration
        sa.Column("config", postgresql.JSONB(none_as_null=True), nullable=True),
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
    op.create_index("ix_am_overnight_runs_project_status", "am_overnight_runs", ["project_id", "status"])
    op.create_index("ix_am_overnight_runs_project_scheduled", "am_overnight_runs", ["project_id", "scheduled_for"])

    # ==========================================================================
    # ARTIFACTS
    # ==========================================================================

    op.create_table(
        "am_artifacts",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        # Source associations
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("overnight_run_id", sa.UUID(), nullable=True),
        # Type
        sa.Column(
            "artifact_type",
            sa.Enum("file", "code", "data", "document", "image", "output", name="am_artifact_type"),
            nullable=False,
        ),
        # Basic info
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # File info
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        # Scope
        sa.Column(
            "scope",
            sa.Enum("personal", "team", "public", name="am_artifact_scope"),
            server_default="personal",
            nullable=False,
        ),
        # Versioning
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("is_final", sa.Boolean(), server_default="false"),
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
            ["project_id", "session_id"],
            ["am_sessions.project_id", "am_sessions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "overnight_run_id"],
            ["am_overnight_runs.project_id", "am_overnight_runs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "parent_id"],
            ["am_artifacts.project_id", "am_artifacts.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_am_artifacts_project_session", "am_artifacts", ["project_id", "session_id"])
    op.create_index("ix_am_artifacts_project_overnight", "am_artifacts", ["project_id", "overnight_run_id"])
    op.create_index("ix_am_artifacts_project_type", "am_artifacts", ["project_id", "artifact_type"])
    op.create_index("ix_am_artifacts_project_scope", "am_artifacts", ["project_id", "scope"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("am_artifacts")
    op.drop_table("am_overnight_runs")
    op.drop_table("am_monitoring_sessions")
    op.drop_table("am_meta_sessions")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS am_artifact_scope")
    op.execute("DROP TYPE IF EXISTS am_artifact_type")
    op.execute("DROP TYPE IF EXISTS am_overnight_run_status")
    op.execute("DROP TYPE IF EXISTS am_monitoring_session_status")
    op.execute("DROP TYPE IF EXISTS am_monitoring_type")
    op.execute("DROP TYPE IF EXISTS am_meta_session_status")
    op.execute("DROP TYPE IF EXISTS am_meta_session_type")
