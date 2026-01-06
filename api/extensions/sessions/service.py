"""
Agent Matrix - Sessions Service

Business logic for session management.
"""

from typing import Optional, List
from uuid import UUID

from oss.src.utils.logging import get_module_logger

from extensions.sessions.dao import SessionsDAO
from extensions.sessions.types import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionQuery,
    SessionStatus,
    SessionMessage,
    SessionMessageCreate,
)

log = get_module_logger(__name__)


class SessionsService:
    """Service for session operations."""

    def __init__(self):
        self.dao = SessionsDAO()

    # -------------------------------------------------------------------------
    # Session CRUD
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: SessionCreate,
    ) -> Session:
        """Create a new session."""
        log.info(f"Creating session of type {dto.session_type} for project {project_id}")
        return await self.dao.create_session(
            project_id=project_id,
            user_id=user_id,
            dto=dto,
        )

    async def get_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
    ) -> Optional[Session]:
        """Get a session by ID."""
        return await self.dao.get_session(
            project_id=project_id,
            session_id=session_id,
        )

    async def list_sessions(
        self,
        *,
        project_id: UUID,
        query: SessionQuery,
    ) -> List[Session]:
        """List sessions with optional filtering."""
        return await self.dao.list_sessions(
            project_id=project_id,
            query=query,
        )

    async def update_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
        dto: SessionUpdate,
    ) -> Optional[Session]:
        """Update a session."""
        return await self.dao.update_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=dto,
        )

    async def delete_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a session."""
        log.info(f"Deleting session {session_id}")
        return await self.dao.delete_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
        )

    # -------------------------------------------------------------------------
    # Session Status Management
    # -------------------------------------------------------------------------

    async def start_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[Session]:
        """Mark a session as running."""
        log.info(f"Starting session {session_id}")
        return await self.dao.update_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=SessionUpdate(status=SessionStatus.RUNNING),
        )

    async def complete_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
        output: Optional[str] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost: float = 0.0,
        duration_ms: int = 0,
    ) -> Optional[Session]:
        """Mark a session as completed."""
        log.info(f"Completing session {session_id}")
        from decimal import Decimal
        return await self.dao.update_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=SessionUpdate(
                status=SessionStatus.COMPLETED,
                output=output,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=Decimal(str(cost)),
                duration_ms=duration_ms,
            ),
        )

    async def fail_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
        error: Optional[str] = None,
    ) -> Optional[Session]:
        """Mark a session as failed."""
        log.info(f"Failing session {session_id}: {error}")
        return await self.dao.update_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=SessionUpdate(
                status=SessionStatus.FAILED,
                output=error,
            ),
        )

    async def cancel_session(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[Session]:
        """Mark a session as cancelled."""
        log.info(f"Cancelling session {session_id}")
        return await self.dao.update_session(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=SessionUpdate(status=SessionStatus.CANCELLED),
        )

    # -------------------------------------------------------------------------
    # Messages
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
        return await self.dao.add_message(
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            dto=dto,
        )

    async def get_messages(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
    ) -> List[SessionMessage]:
        """Get all messages for a session."""
        return await self.dao.get_messages(
            project_id=project_id,
            session_id=session_id,
        )

    # -------------------------------------------------------------------------
    # Session Hierarchy
    # -------------------------------------------------------------------------

    async def get_child_sessions(
        self,
        *,
        project_id: UUID,
        parent_session_id: UUID,
    ) -> List[Session]:
        """Get child sessions of a parent session."""
        return await self.dao.get_child_sessions(
            project_id=project_id,
            parent_session_id=parent_session_id,
        )

    async def get_session_tree(
        self,
        *,
        project_id: UUID,
        session_id: UUID,
    ) -> dict:
        """Get a session with all its children recursively."""
        session = await self.get_session(
            project_id=project_id,
            session_id=session_id,
        )
        if not session:
            return {}

        children = await self.get_child_sessions(
            project_id=project_id,
            parent_session_id=session_id,
        )

        child_trees = []
        for child in children:
            child_tree = await self.get_session_tree(
                project_id=project_id,
                session_id=child.id,
            )
            child_trees.append(child_tree)

        return {
            "session": session,
            "children": child_trees,
        }
