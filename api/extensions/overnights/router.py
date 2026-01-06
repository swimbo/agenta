"""
Agent Matrix - Overnight Runs Router

REST API endpoints for overnight run operations.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks

from extensions.overnights.service import OvernightsService
from extensions.overnights.types import (
    OvernightRunCreate,
    OvernightRunUpdate,
    OvernightRun,
    OvernightRunProgress,
    OvernightRunStatus,
)


class OvernightsRouter:
    """Router for overnight run operations."""

    def __init__(self, service: OvernightsService):
        self.service = service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        router = self.router

        @router.post("", response_model=OvernightRun)
        async def create_overnight_run(
            payload: OvernightRunCreate,
            request: Request,
        ):
            """Create a new overnight run."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.create_overnight_run(
                    session, project_id, payload, user_id
                )
                await session.commit()
                return result

        @router.get("", response_model=list[OvernightRun])
        async def list_overnight_runs(
            request: Request,
            status: Optional[OvernightRunStatus] = Query(None),
            scheduled_after: Optional[datetime] = Query(None),
            scheduled_before: Optional[datetime] = Query(None),
            limit: int = Query(100, le=1000),
            offset: int = Query(0),
        ):
            """List overnight runs with optional filters."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                return await self.service.list_overnight_runs(
                    session,
                    project_id,
                    status.value if status else None,
                    scheduled_after,
                    scheduled_before,
                    limit,
                    offset,
                )

        @router.get("/{run_id}", response_model=OvernightRun)
        async def get_overnight_run(
            run_id: UUID,
            request: Request,
        ):
            """Get an overnight run by ID."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.get_overnight_run(
                    session, project_id, run_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Overnight run not found")
                return result

        @router.patch("/{run_id}", response_model=OvernightRun)
        async def update_overnight_run(
            run_id: UUID,
            payload: OvernightRunUpdate,
            request: Request,
        ):
            """Update an overnight run."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.update_overnight_run(
                    session, project_id, run_id, payload, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Overnight run not found")
                await session.commit()
                return result

        @router.delete("/{run_id}", status_code=204)
        async def delete_overnight_run(
            run_id: UUID,
            request: Request,
        ):
            """Delete an overnight run."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                deleted = await self.service.delete_overnight_run(
                    session, project_id, run_id, user_id
                )
                if not deleted:
                    raise HTTPException(status_code=404, detail="Overnight run not found")
                await session.commit()

        @router.get("/{run_id}/progress", response_model=OvernightRunProgress)
        async def get_progress(
            run_id: UUID,
            request: Request,
        ):
            """Get progress information for an overnight run."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.get_progress(session, project_id, run_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Overnight run not found")
                return result

        @router.post("/{run_id}/start", response_model=OvernightRun)
        async def start_overnight_run(
            run_id: UUID,
            request: Request,
            background_tasks: BackgroundTasks,
        ):
            """Start an overnight run (begins execution in background)."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                try:
                    result = await self.service.start_overnight_run(
                        session, project_id, run_id
                    )
                    if not result:
                        raise HTTPException(status_code=404, detail="Overnight run not found")
                    await session.commit()

                    # Note: In production, this would be handled by a task queue (Taskiq/Celery)
                    # background_tasks.add_task(execute_in_background, project_id, run_id)

                    return result
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))

        @router.post("/{run_id}/pause", response_model=OvernightRun)
        async def pause_overnight_run(
            run_id: UUID,
            request: Request,
        ):
            """Pause a running overnight run."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                try:
                    result = await self.service.pause_overnight_run(
                        session, project_id, run_id
                    )
                    if not result:
                        raise HTTPException(status_code=404, detail="Overnight run not found")
                    await session.commit()
                    return result
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))

        @router.post("/{run_id}/resume", response_model=OvernightRun)
        async def resume_overnight_run(
            run_id: UUID,
            request: Request,
        ):
            """Resume a paused overnight run."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                try:
                    result = await self.service.resume_overnight_run(
                        session, project_id, run_id
                    )
                    if not result:
                        raise HTTPException(status_code=404, detail="Overnight run not found")
                    await session.commit()
                    return result
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))

        @router.post("/{run_id}/cancel", response_model=OvernightRun)
        async def cancel_overnight_run(
            run_id: UUID,
            request: Request,
        ):
            """Cancel an overnight run."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                try:
                    result = await self.service.cancel_overnight_run(
                        session, project_id, run_id
                    )
                    if not result:
                        raise HTTPException(status_code=404, detail="Overnight run not found")
                    await session.commit()
                    return result
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
