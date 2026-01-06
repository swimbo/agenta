"""
Agent Matrix - Artifacts Types

Pydantic models for artifact operations.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class ArtifactType(str, Enum):
    """Artifact types."""
    FILE = "file"
    CODE = "code"
    DATA = "data"
    DOCUMENT = "document"
    IMAGE = "image"
    OUTPUT = "output"


class ArtifactScope(str, Enum):
    """Artifact scope."""
    PERSONAL = "personal"
    TEAM = "team"
    PUBLIC = "public"


class ArtifactCreate(BaseModel):
    """Create an artifact."""
    artifact_type: ArtifactType
    name: str
    description: Optional[str] = None
    session_id: Optional[UUID] = None
    overnight_run_id: Optional[UUID] = None
    mime_type: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    size_bytes: Optional[int] = None
    scope: ArtifactScope = ArtifactScope.PERSONAL
    parent_id: Optional[UUID] = None  # For versioning
    is_final: bool = False
    tags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = None


class ArtifactUpdate(BaseModel):
    """Update an artifact."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    scope: Optional[ArtifactScope] = None
    is_final: Optional[bool] = None
    tags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = None


class Artifact(BaseModel):
    """Artifact response."""
    id: UUID
    project_id: UUID
    artifact_type: ArtifactType
    name: str
    description: Optional[str] = None
    session_id: Optional[UUID] = None
    overnight_run_id: Optional[UUID] = None
    mime_type: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    size_bytes: Optional[int] = None
    scope: ArtifactScope
    parent_id: Optional[UUID] = None
    version: int = 1
    is_final: bool = False
    tags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ArtifactVersionHistory(BaseModel):
    """Artifact version history."""
    artifact_id: UUID
    versions: list[Artifact]
    total_versions: int
