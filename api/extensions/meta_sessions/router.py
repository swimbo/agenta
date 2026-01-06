"""
Agent Matrix - Meta Sessions Router

REST API endpoints for meta sessions and monitoring sessions.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException

from extensions.meta_sessions.service import MetaSessionsService
from extensions.meta_sessions.types import (
    MetaSessionCreate,
    MetaSessionUpdate,
    MetaSession,
    MetaSessionWithMonitoring,
    MonitoringSessionCreate,
    MonitoringSessionUpdate,
    MonitoringSession,
    MetaSessionType,
    MetaSessionStatus,
    MonitoringType,
    MonitoringSessionStatus,
)


class MetaSessionsRouter:
    """Router for meta session operations."""

    def __init__(self, service: MetaSessionsService):
        self.service = service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        router = self.router

        # =====================================================================
        # Meta Sessions
        # =====================================================================

        @router.post("", response_model=MetaSessionWithMonitoring)
        async def create_meta_session(
            payload: MetaSessionCreate,
            request: Request,
        ):
            """Create a new meta session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.create_meta_session(
                    session, project_id, payload, user_id
                )
                await session.commit()
                return result

        @router.get("", response_model=list[MetaSession])
        async def list_meta_sessions(
            request: Request,
            meta_type: Optional[MetaSessionType] = Query(None),
            status: Optional[MetaSessionStatus] = Query(None),
            limit: int = Query(100, le=1000),
            offset: int = Query(0),
        ):
            """List meta sessions with optional filters."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                return await self.service.list_meta_sessions(
                    session,
                    project_id,
                    meta_type.value if meta_type else None,
                    status.value if status else None,
                    limit,
                    offset,
                )

        @router.get("/{meta_session_id}", response_model=MetaSessionWithMonitoring)
        async def get_meta_session(
            meta_session_id: UUID,
            request: Request,
        ):
            """Get a meta session by ID with its monitoring sessions."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.get_meta_session_with_monitoring(
                    session, project_id, meta_session_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Meta session not found")
                return result

        @router.patch("/{meta_session_id}", response_model=MetaSession)
        async def update_meta_session(
            meta_session_id: UUID,
            payload: MetaSessionUpdate,
            request: Request,
        ):
            """Update a meta session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.update_meta_session(
                    session, project_id, meta_session_id, payload, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Meta session not found")
                await session.commit()
                return result

        @router.post("/{meta_session_id}/stop", response_model=MetaSession)
        async def stop_meta_session(
            meta_session_id: UUID,
            request: Request,
        ):
            """Stop a meta session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.stop_meta_session(
                    session, project_id, meta_session_id, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Meta session not found")
                await session.commit()
                return result

        @router.delete("/{meta_session_id}", status_code=204)
        async def delete_meta_session(
            meta_session_id: UUID,
            request: Request,
        ):
            """Delete a meta session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                deleted = await self.service.delete_meta_session(
                    session, project_id, meta_session_id, user_id
                )
                if not deleted:
                    raise HTTPException(status_code=404, detail="Meta session not found")
                await session.commit()

        # =====================================================================
        # Monitoring Sessions
        # =====================================================================

        @router.post("/{meta_session_id}/monitoring", response_model=MonitoringSession)
        async def create_monitoring_session(
            meta_session_id: UUID,
            payload: MonitoringSessionCreate,
            request: Request,
        ):
            """Create a monitoring session for a meta session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            # Override target_meta_session_id from path
            payload.target_meta_session_id = meta_session_id

            async with request.state.session as session:
                result = await self.service.create_monitoring_session(
                    session, project_id, payload, user_id
                )
                await session.commit()
                return result

        @router.get("/{meta_session_id}/monitoring", response_model=list[MonitoringSession])
        async def list_monitoring_sessions(
            meta_session_id: UUID,
            request: Request,
            monitoring_type: Optional[MonitoringType] = Query(None),
            status: Optional[MonitoringSessionStatus] = Query(None),
        ):
            """List monitoring sessions for a meta session."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                return await self.service.list_monitoring_sessions(
                    session,
                    project_id,
                    meta_session_id,
                    monitoring_type.value if monitoring_type else None,
                    status.value if status else None,
                )

        @router.get("/monitoring/{monitoring_session_id}", response_model=MonitoringSession)
        async def get_monitoring_session(
            monitoring_session_id: UUID,
            request: Request,
        ):
            """Get a monitoring session by ID."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.get_monitoring_session(
                    session, project_id, monitoring_session_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Monitoring session not found")
                return result

        @router.patch("/monitoring/{monitoring_session_id}", response_model=MonitoringSession)
        async def update_monitoring_session(
            monitoring_session_id: UUID,
            payload: MonitoringSessionUpdate,
            request: Request,
        ):
            """Update a monitoring session."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.update_monitoring_session(
                    session, project_id, monitoring_session_id, payload, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Monitoring session not found")
                await session.commit()
                return result

        @router.post("/monitoring/{monitoring_session_id}/start", response_model=MonitoringSession)
        async def start_monitoring(
            monitoring_session_id: UUID,
            request: Request,
        ):
            """Start a monitoring session."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.start_monitoring(
                    session, project_id, monitoring_session_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Monitoring session not found")
                await session.commit()
                return result
