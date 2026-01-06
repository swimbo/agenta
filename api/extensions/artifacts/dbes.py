"""
Agent Matrix - Artifacts Database Entities

Artifacts are outputs from sessions and overnight runs with versioning support.
"""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    BigInteger,
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


class ArtifactDBE(Base, ProjectScopeDBA, LifecycleDBA, IdentifierDBA, TagsDBA, MetaDBA):
    """
    Artifact entity.

    Stores outputs from sessions and overnight runs with versioning support.
    """
    __tablename__ = "am_artifacts"

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
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["project_id", "overnight_run_id"],
            ["am_overnight_runs.project_id", "am_overnight_runs.id"],
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["project_id", "parent_id"],
            ["am_artifacts.project_id", "am_artifacts.id"],
            ondelete="SET NULL",
        ),
        Index("ix_am_artifacts_project_id_session_id", "project_id", "session_id"),
        Index("ix_am_artifacts_project_id_overnight_run_id", "project_id", "overnight_run_id"),
        Index("ix_am_artifacts_project_id_type", "project_id", "artifact_type"),
        Index("ix_am_artifacts_project_id_scope", "project_id", "scope"),
    )

    # Source associations
    session_id = Column(UUID(as_uuid=True), nullable=True)
    overnight_run_id = Column(UUID(as_uuid=True), nullable=True)

    # Artifact type
    artifact_type = Column(
        Enum("file", "code", "data", "document", "image", "output", name="am_artifact_type"),
        nullable=False,
    )

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # File info
    mime_type = Column(String(100), nullable=True)
    file_path = Column(String(1024), nullable=True)
    content = Column(Text, nullable=True)  # For small artifacts
    size_bytes = Column(BigInteger, nullable=True)

    # Scope
    scope = Column(
        Enum("personal", "team", "public", name="am_artifact_scope"),
        default="personal",
        nullable=False,
    )

    # Versioning
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # Previous version
    version = Column(Integer, default=1)
    is_final = Column(Boolean, default=False)
