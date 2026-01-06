"""
Agent Matrix - Sessions Router

FastAPI router for session endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from oss.src.utils.logging import get_module_logger
from oss.src.apis.fastapi.shared.utils import handle_exceptions
from oss.src.core.shared.dtos import ProjectScopeDTO

from extensions.sessions.service import SessionsService
from extensions.sessions.types import (
    SessionCreate,
    SessionQuery,
    SessionType,
    SessionStatus,
    MessageRole,
    SessionMessageCreate,
    SessionCreateRequest,
    SessionResponse,
    SessionsListResponse,
    SessionMessageResponse,
    SessionMessageCreateRequest,
)

log = get_module_logger(__name__)


class SessionsRouter:
    """Router for session endpoints."""

    def __init__(self):
        self.service = SessionsService()
        self.router = APIRouter(prefix="/sessions", tags=["Sessions"])
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("", response_model=SessionResponse)
        @handle_exceptions
        async def create_session(
            request: SessionCreateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Create a new session."""
            dto = SessionCreate(
                agent_id=UUID(request.agent_id) if request.agent_id else None,
                workflow_id=UUID(request.workflow_id) if request.workflow_id else None,
                parent_session_id=UUID(request.parent_session_id) if request.parent_session_id else None,
                meta_session_id=UUID(request.meta_session_id) if request.meta_session_id else None,
                session_type=SessionType(request.session_type) if request.session_type else None,
                input=request.input,
                meta=request.meta,
            )

            session = await self.service.create_session(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            return SessionResponse.from_dto(session)

        @self.router.get("", response_model=SessionsListResponse)
        @handle_exceptions
        async def list_sessions(
            project_scope: ProjectScopeDTO = Depends(),
            agent_id: Optional[str] = Query(None),
            workflow_id: Optional[str] = Query(None),
            parent_session_id: Optional[str] = Query(None),
            meta_session_id: Optional[str] = Query(None),
            session_type: Optional[str] = Query(None),
            status: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=100),
        ):
            """List sessions."""
            query = SessionQuery(
                agent_id=UUID(agent_id) if agent_id else None,
                workflow_id=UUID(workflow_id) if workflow_id else None,
                parent_session_id=UUID(parent_session_id) if parent_session_id else None,
                meta_session_id=UUID(meta_session_id) if meta_session_id else None,
                session_type=SessionType(session_type) if session_type else None,
                status=SessionStatus(status) if status else None,
                offset=offset,
                limit=limit,
            )
            sessions = await self.service.list_sessions(
                project_id=project_scope.project_id,
                query=query,
            )
            return SessionsListResponse(
                sessions=[SessionResponse.from_dto(s) for s in sessions],
                total=len(sessions),
                offset=offset,
                limit=limit,
            )

        @self.router.get("/{session_id}", response_model=SessionResponse)
        @handle_exceptions
        async def get_session(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get a session by ID."""
            session = await self.service.get_session(
                project_id=project_scope.project_id,
                session_id=session_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return SessionResponse.from_dto(session)

        @self.router.delete("/{session_id}")
        @handle_exceptions
        async def delete_session(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Delete a session."""
            deleted = await self.service.delete_session(
                project_id=project_scope.project_id,
                session_id=session_id,
                user_id=project_scope.user_id,
            )
            if not deleted:
                raise HTTPException(status_code=404, detail="Session not found")
            return {"success": True}

        # Status endpoints
        @self.router.post("/{session_id}/start", response_model=SessionResponse)
        @handle_exceptions
        async def start_session(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Start a session (mark as running)."""
            session = await self.service.start_session(
                project_id=project_scope.project_id,
                session_id=session_id,
                user_id=project_scope.user_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return SessionResponse.from_dto(session)

        @self.router.post("/{session_id}/cancel", response_model=SessionResponse)
        @handle_exceptions
        async def cancel_session(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Cancel a session."""
            session = await self.service.cancel_session(
                project_id=project_scope.project_id,
                session_id=session_id,
                user_id=project_scope.user_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return SessionResponse.from_dto(session)

        # Message endpoints
        @self.router.get("/{session_id}/messages")
        @handle_exceptions
        async def get_messages(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get all messages for a session."""
            messages = await self.service.get_messages(
                project_id=project_scope.project_id,
                session_id=session_id,
            )
            return {
                "messages": [SessionMessageResponse.from_dto(m) for m in messages],
                "total": len(messages),
            }

        @self.router.post("/{session_id}/messages", response_model=SessionMessageResponse)
        @handle_exceptions
        async def add_message(
            session_id: UUID,
            request: SessionMessageCreateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Add a message to a session."""
            dto = SessionMessageCreate(
                role=MessageRole(request.role),
                content=request.content,
                tool_calls=request.tool_calls,
            )
            message = await self.service.add_message(
                project_id=project_scope.project_id,
                session_id=session_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            return SessionMessageResponse.from_dto(message)

        # Hierarchy endpoints
        @self.router.get("/{session_id}/children")
        @handle_exceptions
        async def get_child_sessions(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get child sessions of a parent session."""
            children = await self.service.get_child_sessions(
                project_id=project_scope.project_id,
                parent_session_id=session_id,
            )
            return {
                "sessions": [SessionResponse.from_dto(s) for s in children],
                "total": len(children),
            }

        @self.router.get("/{session_id}/tree")
        @handle_exceptions
        async def get_session_tree(
            session_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get session with all children recursively."""
            tree = await self.service.get_session_tree(
                project_id=project_scope.project_id,
                session_id=session_id,
            )
            if not tree:
                raise HTTPException(status_code=404, detail="Session not found")
            return tree
