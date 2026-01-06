"""
Agent Matrix - Meta Sessions Service

Business logic for meta sessions and monitoring sessions.
"""

from typing import Optional
from uuid import UUID

from extensions.meta_sessions.dao import MetaSessionsDAO
from extensions.meta_sessions.types import (
    MetaSessionCreate,
    MetaSessionUpdate,
    MetaSession,
    MonitoringSessionCreate,
    MonitoringSessionUpdate,
    MonitoringSession,
    MetaSessionWithMonitoring,
    MonitoringType,
)


class MetaSessionsService:
    """Service for meta session operations."""

    def __init__(self, dao: MetaSessionsDAO, agents_service=None):
        self.dao = dao
        self.agents_service = agents_service

    async def create_meta_session(
        self,
        session,  # AsyncSession
        project_id: UUID,
        dto: MetaSessionCreate,
        created_by_id: Optional[UUID] = None,
    ) -> MetaSessionWithMonitoring:
        """
        Create a meta session.

        If auto_start_guardrails is True and we have an agents service,
        automatically starts a guardrails monitoring session.
        """
        meta = await self.dao.create_meta_session(
            session, project_id, dto, created_by_id
        )

        monitoring_sessions = []

        # Auto-start guardrails agent if configured
        if dto.auto_start_guardrails and self.agents_service:
            guardrails_agent = await self._get_guardrails_agent(
                session, project_id
            )
            if guardrails_agent:
                monitoring = await self.dao.create_monitoring_session(
                    session,
                    project_id,
                    MonitoringSessionCreate(
                        target_meta_session_id=meta.id,
                        monitoring_type=MonitoringType.GUARDRAILS,
                        agent_id=guardrails_agent.id,
                        auto_started=True,
                    ),
                    created_by_id,
                )
                monitoring_sessions.append(monitoring)

        return MetaSessionWithMonitoring(
            **meta.model_dump(),
            monitoring_sessions=monitoring_sessions,
        )

    async def get_meta_session(
        self,
        session,
        project_id: UUID,
        meta_session_id: UUID,
    ) -> Optional[MetaSession]:
        """Get a meta session by ID."""
        return await self.dao.get_meta_session(session, project_id, meta_session_id)

    async def get_meta_session_with_monitoring(
        self,
        session,
        project_id: UUID,
        meta_session_id: UUID,
    ) -> Optional[MetaSessionWithMonitoring]:
        """Get a meta session with its monitoring sessions."""
        return await self.dao.get_meta_session_with_monitoring(
            session, project_id, meta_session_id
        )

    async def list_meta_sessions(
        self,
        session,
        project_id: UUID,
        meta_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetaSession]:
        """List meta sessions with optional filters."""
        return await self.dao.list_meta_sessions(
            session, project_id, meta_type, status, limit, offset
        )

    async def update_meta_session(
        self,
        session,
        project_id: UUID,
        meta_session_id: UUID,
        dto: MetaSessionUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[MetaSession]:
        """Update a meta session."""
        return await self.dao.update_meta_session(
            session, project_id, meta_session_id, dto, updated_by_id
        )

    async def stop_meta_session(
        self,
        session,
        project_id: UUID,
        meta_session_id: UUID,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[MetaSession]:
        """Stop a meta session."""
        return await self.dao.update_meta_session(
            session,
            project_id,
            meta_session_id,
            MetaSessionUpdate(status="stopped"),
            updated_by_id,
        )

    async def delete_meta_session(
        self,
        session,
        project_id: UUID,
        meta_session_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Delete a meta session."""
        return await self.dao.delete_meta_session(
            session, project_id, meta_session_id, deleted_by_id
        )

    # -------------------------------------------------------------------------
    # Monitoring Sessions
    # -------------------------------------------------------------------------

    async def create_monitoring_session(
        self,
        session,
        project_id: UUID,
        dto: MonitoringSessionCreate,
        created_by_id: Optional[UUID] = None,
    ) -> MonitoringSession:
        """Create a monitoring session."""
        return await self.dao.create_monitoring_session(
            session, project_id, dto, created_by_id
        )

    async def get_monitoring_session(
        self,
        session,
        project_id: UUID,
        monitoring_session_id: UUID,
    ) -> Optional[MonitoringSession]:
        """Get a monitoring session by ID."""
        return await self.dao.get_monitoring_session(
            session, project_id, monitoring_session_id
        )

    async def list_monitoring_sessions(
        self,
        session,
        project_id: UUID,
        target_meta_session_id: Optional[UUID] = None,
        monitoring_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[MonitoringSession]:
        """List monitoring sessions with optional filters."""
        return await self.dao.list_monitoring_sessions(
            session, project_id, target_meta_session_id, monitoring_type, status
        )

    async def update_monitoring_session(
        self,
        session,
        project_id: UUID,
        monitoring_session_id: UUID,
        dto: MonitoringSessionUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[MonitoringSession]:
        """Update a monitoring session."""
        return await self.dao.update_monitoring_session(
            session, project_id, monitoring_session_id, dto, updated_by_id
        )

    async def start_monitoring(
        self,
        session,
        project_id: UUID,
        monitoring_session_id: UUID,
    ) -> Optional[MonitoringSession]:
        """Start a monitoring session."""
        return await self.dao.update_monitoring_session(
            session,
            project_id,
            monitoring_session_id,
            MonitoringSessionUpdate(status="running"),
        )

    async def complete_monitoring(
        self,
        session,
        project_id: UUID,
        monitoring_session_id: UUID,
        results: dict,
    ) -> Optional[MonitoringSession]:
        """Complete a monitoring session with results."""
        return await self.dao.update_monitoring_session(
            session,
            project_id,
            monitoring_session_id,
            MonitoringSessionUpdate(status="completed", results=results),
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def _get_guardrails_agent(self, session, project_id: UUID):
        """Get the Guard Rails agent if available."""
        if not self.agents_service:
            return None

        # Try to find agent by name
        agents = await self.agents_service.list_agents(
            session, project_id, name="Guard Rails"
        )
        return agents[0] if agents else None
