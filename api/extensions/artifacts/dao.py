"""
Agent Matrix - Artifacts DAO

Data access layer for artifacts.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid_utils.compat as uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from extensions.artifacts.dbes import ArtifactDBE
from extensions.artifacts.types import (
    ArtifactCreate,
    ArtifactUpdate,
    Artifact,
    ArtifactVersionHistory,
)


class ArtifactsDAO:
    """Data access for artifacts."""

    async def create(
        self,
        session: AsyncSession,
        project_id: UUID,
        dto: ArtifactCreate,
        created_by_id: Optional[UUID] = None,
    ) -> Artifact:
        """Create a new artifact."""
        # Determine version number
        version = 1
        if dto.parent_id:
            parent = await self.get(session, project_id, dto.parent_id)
            if parent:
                version = parent.version + 1

        dbe = ArtifactDBE(
            id=uuid.uuid7(),
            project_id=project_id,
            artifact_type=dto.artifact_type.value,
            name=dto.name,
            description=dto.description,
            session_id=dto.session_id,
            overnight_run_id=dto.overnight_run_id,
            mime_type=dto.mime_type,
            file_path=dto.file_path,
            content=dto.content,
            size_bytes=dto.size_bytes,
            scope=dto.scope.value,
            parent_id=dto.parent_id,
            version=version,
            is_final=dto.is_final,
            tags=dto.tags,
            meta=dto.meta,
            created_by_id=created_by_id,
        )
        session.add(dbe)
        await session.flush()
        return self._to_dto(dbe)

    async def get(
        self,
        session: AsyncSession,
        project_id: UUID,
        artifact_id: UUID,
    ) -> Optional[Artifact]:
        """Get an artifact by ID."""
        query = select(ArtifactDBE).where(
            and_(
                ArtifactDBE.project_id == project_id,
                ArtifactDBE.id == artifact_id,
                ArtifactDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        return self._to_dto(dbe) if dbe else None

    async def list(
        self,
        session: AsyncSession,
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
        query = select(ArtifactDBE).where(
            and_(
                ArtifactDBE.project_id == project_id,
                ArtifactDBE.deleted_at.is_(None),
            )
        )

        if session_id:
            query = query.where(ArtifactDBE.session_id == session_id)
        if overnight_run_id:
            query = query.where(ArtifactDBE.overnight_run_id == overnight_run_id)
        if artifact_type:
            query = query.where(ArtifactDBE.artifact_type == artifact_type)
        if scope:
            query = query.where(ArtifactDBE.scope == scope)
        if is_final is not None:
            query = query.where(ArtifactDBE.is_final == is_final)

        query = query.order_by(ArtifactDBE.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        return [self._to_dto(dbe) for dbe in result.scalars()]

    async def update(
        self,
        session: AsyncSession,
        project_id: UUID,
        artifact_id: UUID,
        dto: ArtifactUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Artifact]:
        """Update an artifact."""
        query = select(ArtifactDBE).where(
            and_(
                ArtifactDBE.project_id == project_id,
                ArtifactDBE.id == artifact_id,
                ArtifactDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return None

        if dto.name is not None:
            dbe.name = dto.name
        if dto.description is not None:
            dbe.description = dto.description
        if dto.content is not None:
            dbe.content = dto.content
        if dto.scope is not None:
            dbe.scope = dto.scope.value
        if dto.is_final is not None:
            dbe.is_final = dto.is_final
        if dto.tags is not None:
            dbe.tags = dto.tags
        if dto.meta is not None:
            dbe.meta = dto.meta

        dbe.updated_at = datetime.utcnow()
        dbe.updated_by_id = updated_by_id

        await session.flush()
        return self._to_dto(dbe)

    async def delete(
        self,
        session: AsyncSession,
        project_id: UUID,
        artifact_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an artifact."""
        query = select(ArtifactDBE).where(
            and_(
                ArtifactDBE.project_id == project_id,
                ArtifactDBE.id == artifact_id,
                ArtifactDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return False

        dbe.deleted_at = datetime.utcnow()
        dbe.deleted_by_id = deleted_by_id
        await session.flush()
        return True

    async def get_version_history(
        self,
        session: AsyncSession,
        project_id: UUID,
        artifact_id: UUID,
    ) -> ArtifactVersionHistory:
        """Get version history for an artifact."""
        # First, find the root artifact
        artifact = await self.get(session, project_id, artifact_id)
        if not artifact:
            return ArtifactVersionHistory(
                artifact_id=artifact_id,
                versions=[],
                total_versions=0,
            )

        # Trace back to root
        root_id = artifact_id
        current = artifact
        while current.parent_id:
            root_id = current.parent_id
            current = await self.get(session, project_id, current.parent_id)
            if not current:
                break

        # Get all versions from root
        versions = [current] if current else []
        children = await self._get_children(session, project_id, root_id)
        versions.extend(children)

        # Sort by version
        versions.sort(key=lambda v: v.version)

        return ArtifactVersionHistory(
            artifact_id=root_id,
            versions=versions,
            total_versions=len(versions),
        )

    async def _get_children(
        self,
        session: AsyncSession,
        project_id: UUID,
        parent_id: UUID,
    ) -> list[Artifact]:
        """Get all child versions recursively."""
        query = select(ArtifactDBE).where(
            and_(
                ArtifactDBE.project_id == project_id,
                ArtifactDBE.parent_id == parent_id,
                ArtifactDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        children = [self._to_dto(dbe) for dbe in result.scalars()]

        all_children = list(children)
        for child in children:
            grandchildren = await self._get_children(session, project_id, child.id)
            all_children.extend(grandchildren)

        return all_children

    def _to_dto(self, dbe: ArtifactDBE) -> Artifact:
        return Artifact(
            id=dbe.id,
            project_id=dbe.project_id,
            artifact_type=dbe.artifact_type,
            name=dbe.name,
            description=dbe.description,
            session_id=dbe.session_id,
            overnight_run_id=dbe.overnight_run_id,
            mime_type=dbe.mime_type,
            file_path=dbe.file_path,
            content=dbe.content,
            size_bytes=dbe.size_bytes,
            scope=dbe.scope,
            parent_id=dbe.parent_id,
            version=dbe.version,
            is_final=dbe.is_final,
            tags=dbe.tags,
            meta=dbe.meta,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )
