"""
Agent Matrix - Artifacts Service

Business logic for artifact operations.
"""

from typing import Optional
from uuid import UUID

from extensions.artifacts.dao import ArtifactsDAO
from extensions.artifacts.types import (
    ArtifactCreate,
    ArtifactUpdate,
    Artifact,
    ArtifactVersionHistory,
)


class ArtifactsService:
    """Service for artifact operations."""

    def __init__(self, dao: ArtifactsDAO):
        self.dao = dao

    async def create_artifact(
        self,
        session,
        project_id: UUID,
        dto: ArtifactCreate,
        created_by_id: Optional[UUID] = None,
    ) -> Artifact:
        """Create a new artifact."""
        return await self.dao.create(session, project_id, dto, created_by_id)

    async def get_artifact(
        self,
        session,
        project_id: UUID,
        artifact_id: UUID,
    ) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return await self.dao.get(session, project_id, artifact_id)

    async def list_artifacts(
        self,
        session,
        project_id: UUID,
        session_id: Optional[UUID] = None,
        overnight_run_id: Optional[UUID] = None,
        artifact_type: Optional[str] = None,
        scope: Optional[str] = None,
        is_final: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        """List artifacts with optional filters."""
        return await self.dao.list(
            session,
            project_id,
            session_id,
            overnight_run_id,
            artifact_type,
            scope,
            is_final,
            limit,
            offset,
        )

    async def update_artifact(
        self,
        session,
        project_id: UUID,
        artifact_id: UUID,
        dto: ArtifactUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Artifact]:
        """Update an artifact."""
        return await self.dao.update(
            session, project_id, artifact_id, dto, updated_by_id
        )

    async def delete_artifact(
        self,
        session,
        project_id: UUID,
        artifact_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Delete an artifact."""
        return await self.dao.delete(
            session, project_id, artifact_id, deleted_by_id
        )

    async def create_new_version(
        self,
        session,
        project_id: UUID,
        parent_id: UUID,
        dto: ArtifactCreate,
        created_by_id: Optional[UUID] = None,
    ) -> Artifact:
        """Create a new version of an artifact."""
        dto.parent_id = parent_id
        return await self.dao.create(session, project_id, dto, created_by_id)

    async def get_version_history(
        self,
        session,
        project_id: UUID,
        artifact_id: UUID,
    ) -> ArtifactVersionHistory:
        """Get version history for an artifact."""
        return await self.dao.get_version_history(session, project_id, artifact_id)

    async def mark_as_final(
        self,
        session,
        project_id: UUID,
        artifact_id: UUID,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Artifact]:
        """Mark an artifact as final."""
        return await self.dao.update(
            session,
            project_id,
            artifact_id,
            ArtifactUpdate(is_final=True),
            updated_by_id,
        )
