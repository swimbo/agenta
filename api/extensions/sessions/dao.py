"""
Agent Matrix - Sessions Data Access Object

CRUD operations for sessions and messages.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from oss.src.utils.logging import get_module_logger
from oss.src.dbs.postgres.shared.engine import engine

from extensions.sessions.dbes import SessionDBE, SessionMessageDBE
from extensions.sessions.types import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionQuery,
    SessionMessage,
    SessionMessageCreate,
    MessageRole,
)

log = get_module_logger(__name__)


class SessionsDAO:
    """Data access object for sessions and messages."""

    # -------------------------------------------------------------------------
    # Sessions CRUD
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: SessionCreate,
    ) -> Session:
        """Create a new session."""
        async with engine.core_session() as session:
            dbe = SessionDBE(
                project_id=project_id,
                created_by_id=user_id,
                agent_id=dto.agent_id,
                workflow_id=dto.workflow_id,
                parent_session_id=dto.parent_session_id,
                meta_session_id=dto.meta_session_id,
                session_type=dto.session_type.value if dto.session_type else "agent",
                status="pending",
                input=dto.input,
                meta=dto.meta,
            )
            session.add(dbe)
            await session.flush()
            return self._session_to_dto(dbe)

    async def get_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
    ) -> Optional[Session]:
        """Get a session by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(SessionDBE)
                .where(SessionDBE.project_id == project_id)
                .where(SessionDBE.id == session_id)
                .where(SessionDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._session_to_dto(dbe) if dbe else None

    async def list_sessions(
        self,
        *,
        project_id: UUID,
        query: SessionQuery,
    ) -> List[Session]:
        """List sessions with optional filtering."""
        async with engine.core_session() as session:
            stmt = (
                select(SessionDBE)
                .where(SessionDBE.project_id == project_id)
                .where(SessionDBE.deleted_at.is_(None))
            )

            if query.agent_id:
                stmt = stmt.where(SessionDBE.agent_id == query.agent_id)
            if query.workflow_id:
                stmt = stmt.where(SessionDBE.workflow_id == query.workflow_id)
            if query.parent_session_id:
                stmt = stmt.where(SessionDBE.parent_session_id == query.parent_session_id)
            if query.meta_session_id:
                stmt = stmt.where(SessionDBE.meta_session_id == query.meta_session_id)
            if query.session_type:
                stmt = stmt.where(SessionDBE.session_type == query.session_type.value)
            if query.status:
                stmt = stmt.where(SessionDBE.status == query.status.value)

            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            stmt = stmt.order_by(SessionDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._session_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
        dto: SessionUpdate,
    ) -> Optional[Session]:
        """Update a session."""
        async with engine.core_session() as session:
            stmt = (
                select(SessionDBE)
                .where(SessionDBE.project_id == project_id)
                .where(SessionDBE.id == session_id)
                .where(SessionDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            if dto.status is not None:
                dbe.status = dto.status.value
            if dto.output is not None:
                dbe.output = dto.output
            if dto.tokens_input is not None:
                dbe.tokens_input = dto.tokens_input
            if dto.tokens_output is not None:
                dbe.tokens_output = dto.tokens_output
            if dto.cost is not None:
                dbe.cost = dto.cost
            if dto.duration_ms is not None:
                dbe.duration_ms = dto.duration_ms
            if dto.meta is not None:
                dbe.meta = dto.meta

            dbe.updated_by_id = user_id
            await session.flush()
            return self._session_to_dto(dbe)

    async def delete_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a session."""
        async with engine.core_session() as session:
            stmt = (
                update(SessionDBE)
                .where(SessionDBE.project_id == project_id)
                .where(SessionDBE.id == session_id)
                .where(SessionDBE.deleted_at.is_(None))
                .values(
                    deleted_at=func.now(),
                    deleted_by_id=user_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    # -------------------------------------------------------------------------
    # Session Messages
    # -------------------------------------------------------------------------

    async def add_message(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
        dto: SessionMessageCreate,
    ) -> SessionMessage:
        """Add a message to a session."""
        async with engine.core_session() as session:
            dbe = SessionMessageDBE(
                project_id=project_id,
                session_id=session_id,
                created_by_id=user_id,
                role=dto.role.value,
                content=dto.content,
                tool_calls=dto.tool_calls,
                message_meta=dto.message_meta,
            )
            session.add(dbe)
            await session.flush()
            return self._message_to_dto(dbe)

    async def get_messages(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
    ) -> List[SessionMessage]:
        """Get all messages for a session."""
        async with engine.core_session() as session:
            stmt = (
                select(SessionMessageDBE)
                .where(SessionMessageDBE.project_id == project_id)
                .where(SessionMessageDBE.session_id == session_id)
                .order_by(SessionMessageDBE.created_at.asc())
            )
            result = await session.execute(stmt)
            return [self._message_to_dto(dbe) for dbe in result.scalars().all()]

    async def get_child_sessions(
        self,
        *,
        project_id: UUID,
        parent_session_id: UUID,
    ) -> List[Session]:
        """Get all child sessions of a parent session."""
        async with engine.core_session() as session:
            stmt = (
                select(SessionDBE)
                .where(SessionDBE.project_id == project_id)
                .where(SessionDBE.parent_session_id == parent_session_id)
                .where(SessionDBE.deleted_at.is_(None))
                .order_by(SessionDBE.created_at.asc())
            )
            result = await session.execute(stmt)
            return [self._session_to_dto(dbe) for dbe in result.scalars().all()]

    # -------------------------------------------------------------------------
    # DTO Mappings
    # -------------------------------------------------------------------------

    def _session_to_dto(self, dbe: SessionDBE) -> Session:
        """Convert SessionDBE to Session DTO."""
        return Session(
            id=dbe.id,
            project_id=dbe.project_id,
            agent_id=dbe.agent_id,
            workflow_id=dbe.workflow_id,
            parent_session_id=dbe.parent_session_id,
            meta_session_id=dbe.meta_session_id,
            session_type=dbe.session_type,
            status=dbe.status,
            input=dbe.input,
            output=dbe.output,
            tokens_input=dbe.tokens_input or 0,
            tokens_output=dbe.tokens_output or 0,
            cost=dbe.cost or 0,
            duration_ms=dbe.duration_ms or 0,
            meta=dbe.meta,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )

    def _message_to_dto(self, dbe: SessionMessageDBE) -> SessionMessage:
        """Convert SessionMessageDBE to SessionMessage DTO."""
        return SessionMessage(
            id=dbe.id,
            project_id=dbe.project_id,
            session_id=dbe.session_id,
            role=dbe.role,
            content=dbe.content,
            tool_calls=dbe.tool_calls,
            message_meta=dbe.message_meta,
            created_at=dbe.created_at,
        )
