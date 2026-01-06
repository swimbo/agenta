"""
Agent Matrix - Meta Sessions DAO

Data access layer for meta sessions and monitoring sessions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid_utils.compat as uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from extensions.meta_sessions.dbes import MetaSessionDBE, MonitoringSessionDBE
from extensions.meta_sessions.types import (
    MetaSessionCreate,
    MetaSessionUpdate,
    MetaSession,
    MonitoringSessionCreate,
    MonitoringSessionUpdate,
    MonitoringSession,
    MetaSessionWithMonitoring,
)


class MetaSessionsDAO:
    """Data access for meta sessions."""

    # -------------------------------------------------------------------------
    # Meta Sessions
    # -------------------------------------------------------------------------

    async def create_meta_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        dto: MetaSessionCreate,
        created_by_id: Optional[UUID] = None,
    ) -> MetaSession:
        """Create a new meta session."""
        dbe = MetaSessionDBE(
            id=uuid.uuid7(),
            project_id=project_id,
            meta_type=dto.meta_type.value,
            name=dto.name,
            description=dto.description,
            config=dto.config,
            status="active",
            created_by_id=created_by_id,
        )
        session.add(dbe)
        await session.flush()
        return self._meta_session_to_dto(dbe)

    async def get_meta_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        meta_session_id: UUID,
    ) -> Optional[MetaSession]:
        """Get a meta session by ID."""
        query = select(MetaSessionDBE).where(
            and_(
                MetaSessionDBE.project_id == project_id,
                MetaSessionDBE.id == meta_session_id,
                MetaSessionDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        return self._meta_session_to_dto(dbe) if dbe else None

    async def get_meta_session_with_monitoring(
        self,
        session: AsyncSession,
        project_id: UUID,
        meta_session_id: UUID,
    ) -> Optional[MetaSessionWithMonitoring]:
        """Get a meta session with its monitoring sessions."""
        query = (
            select(MetaSessionDBE)
            .options(selectinload(MetaSessionDBE.monitoring_sessions))
            .where(
                and_(
                    MetaSessionDBE.project_id == project_id,
                    MetaSessionDBE.id == meta_session_id,
                    MetaSessionDBE.deleted_at.is_(None),
                )
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return None

        return MetaSessionWithMonitoring(
            **self._meta_session_to_dto(dbe).model_dump(),
            monitoring_sessions=[
                self._monitoring_session_to_dto(m)
                for m in dbe.monitoring_sessions
                if m.deleted_at is None
            ],
        )

    async def list_meta_sessions(
        self,
        session: AsyncSession,
        project_id: UUID,
        meta_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetaSession]:
        """List meta sessions with optional filters."""
        query = select(MetaSessionDBE).where(
            and_(
                MetaSessionDBE.project_id == project_id,
                MetaSessionDBE.deleted_at.is_(None),
            )
        )

        if meta_type:
            query = query.where(MetaSessionDBE.meta_type == meta_type)
        if status:
            query = query.where(MetaSessionDBE.status == status)

        query = query.order_by(MetaSessionDBE.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        return [self._meta_session_to_dto(dbe) for dbe in result.scalars()]

    async def update_meta_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        meta_session_id: UUID,
        dto: MetaSessionUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[MetaSession]:
        """Update a meta session."""
        query = select(MetaSessionDBE).where(
            and_(
                MetaSessionDBE.project_id == project_id,
                MetaSessionDBE.id == meta_session_id,
                MetaSessionDBE.deleted_at.is_(None),
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
        if dto.status is not None:
            dbe.status = dto.status.value
        if dto.config is not None:
            dbe.config = dto.config

        dbe.updated_at = datetime.utcnow()
        dbe.updated_by_id = updated_by_id

        await session.flush()
        return self._meta_session_to_dto(dbe)

    async def delete_meta_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        meta_session_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Soft delete a meta session."""
        query = select(MetaSessionDBE).where(
            and_(
                MetaSessionDBE.project_id == project_id,
                MetaSessionDBE.id == meta_session_id,
                MetaSessionDBE.deleted_at.is_(None),
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

    # -------------------------------------------------------------------------
    # Monitoring Sessions
    # -------------------------------------------------------------------------

    async def create_monitoring_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        dto: MonitoringSessionCreate,
        created_by_id: Optional[UUID] = None,
    ) -> MonitoringSession:
        """Create a new monitoring session."""
        dbe = MonitoringSessionDBE(
            id=uuid.uuid7(),
            project_id=project_id,
            target_meta_session_id=dto.target_meta_session_id,
            monitoring_type=dto.monitoring_type.value,
            agent_id=dto.agent_id,
            auto_started=dto.auto_started,
            status="pending",
            created_by_id=created_by_id,
        )
        session.add(dbe)
        await session.flush()
        return self._monitoring_session_to_dto(dbe)

    async def get_monitoring_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        monitoring_session_id: UUID,
    ) -> Optional[MonitoringSession]:
        """Get a monitoring session by ID."""
        query = select(MonitoringSessionDBE).where(
            and_(
                MonitoringSessionDBE.project_id == project_id,
                MonitoringSessionDBE.id == monitoring_session_id,
                MonitoringSessionDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        return self._monitoring_session_to_dto(dbe) if dbe else None

    async def list_monitoring_sessions(
        self,
        session: AsyncSession,
        project_id: UUID,
        target_meta_session_id: Optional[UUID] = None,
        monitoring_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[MonitoringSession]:
        """List monitoring sessions with optional filters."""
        query = select(MonitoringSessionDBE).where(
            and_(
                MonitoringSessionDBE.project_id == project_id,
                MonitoringSessionDBE.deleted_at.is_(None),
            )
        )

        if target_meta_session_id:
            query = query.where(MonitoringSessionDBE.target_meta_session_id == target_meta_session_id)
        if monitoring_type:
            query = query.where(MonitoringSessionDBE.monitoring_type == monitoring_type)
        if status:
            query = query.where(MonitoringSessionDBE.status == status)

        query = query.order_by(MonitoringSessionDBE.created_at.desc())

        result = await session.execute(query)
        return [self._monitoring_session_to_dto(dbe) for dbe in result.scalars()]

    async def update_monitoring_session(
        self,
        session: AsyncSession,
        project_id: UUID,
        monitoring_session_id: UUID,
        dto: MonitoringSessionUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[MonitoringSession]:
        """Update a monitoring session."""
        query = select(MonitoringSessionDBE).where(
            and_(
                MonitoringSessionDBE.project_id == project_id,
                MonitoringSessionDBE.id == monitoring_session_id,
                MonitoringSessionDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return None

        if dto.status is not None:
            dbe.status = dto.status.value
        if dto.results is not None:
            dbe.results = dto.results

        dbe.updated_at = datetime.utcnow()
        dbe.updated_by_id = updated_by_id

        await session.flush()
        return self._monitoring_session_to_dto(dbe)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _meta_session_to_dto(self, dbe: MetaSessionDBE) -> MetaSession:
        return MetaSession(
            id=dbe.id,
            project_id=dbe.project_id,
            meta_type=dbe.meta_type,
            status=dbe.status,
            name=dbe.name,
            description=dbe.description,
            config=dbe.config,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )

    def _monitoring_session_to_dto(self, dbe: MonitoringSessionDBE) -> MonitoringSession:
        return MonitoringSession(
            id=dbe.id,
            project_id=dbe.project_id,
            target_meta_session_id=dbe.target_meta_session_id,
            monitoring_type=dbe.monitoring_type,
            agent_id=dbe.agent_id,
            auto_started=dbe.auto_started,
            status=dbe.status,
            results=dbe.results,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
        )
