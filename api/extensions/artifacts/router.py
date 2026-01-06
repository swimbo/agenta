"""
Agent Matrix - Artifacts Router

REST API endpoints for artifact operations.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException

from extensions.artifacts.service import ArtifactsService
from extensions.artifacts.types import (
    ArtifactCreate,
    ArtifactUpdate,
    Artifact,
    ArtifactVersionHistory,
    ArtifactType,
    ArtifactScope,
)


class ArtifactsRouter:
    """Router for artifact operations."""

    def __init__(self, service: ArtifactsService):
        self.service = service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        router = self.router

        @router.post("", response_model=Artifact)
        async def create_artifact(
            payload: ArtifactCreate,
            request: Request,
        ):
            """Create a new artifact."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.create_artifact(
                    session, project_id, payload, user_id
                )
                await session.commit()
                return result

        @router.get("", response_model=list[Artifact])
        async def list_artifacts(
            request: Request,
            session_id: Optional[UUID] = Query(None),
            overnight_run_id: Optional[UUID] = Query(None),
            artifact_type: Optional[ArtifactType] = Query(None),
            scope: Optional[ArtifactScope] = Query(None),
            is_final: Optional[bool] = Query(None),
            limit: int = Query(100, le=1000),
            offset: int = Query(0),
        ):
            """List artifacts with optional filters."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                return await self.service.list_artifacts(
                    session,
                    project_id,
                    session_id,
                    overnight_run_id,
                    artifact_type.value if artifact_type else None,
                    scope.value if scope else None,
                    is_final,
                    limit,
                    offset,
                )

        @router.get("/{artifact_id}", response_model=Artifact)
        async def get_artifact(
            artifact_id: UUID,
            request: Request,
        ):
            """Get an artifact by ID."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.get_artifact(
                    session, project_id, artifact_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Artifact not found")
                return result

        @router.patch("/{artifact_id}", response_model=Artifact)
        async def update_artifact(
            artifact_id: UUID,
            payload: ArtifactUpdate,
            request: Request,
        ):
            """Update an artifact."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.update_artifact(
                    session, project_id, artifact_id, payload, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Artifact not found")
                await session.commit()
                return result

        @router.delete("/{artifact_id}", status_code=204)
        async def delete_artifact(
            artifact_id: UUID,
            request: Request,
        ):
            """Delete an artifact."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                deleted = await self.service.delete_artifact(
                    session, project_id, artifact_id, user_id
                )
                if not deleted:
                    raise HTTPException(status_code=404, detail="Artifact not found")
                await session.commit()

        @router.get("/{artifact_id}/versions", response_model=ArtifactVersionHistory)
        async def get_version_history(
            artifact_id: UUID,
            request: Request,
        ):
            """Get version history for an artifact."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                return await self.service.get_version_history(
                    session, project_id, artifact_id
                )

        @router.post("/{artifact_id}/versions", response_model=Artifact)
        async def create_new_version(
            artifact_id: UUID,
            payload: ArtifactCreate,
            request: Request,
        ):
            """Create a new version of an artifact."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.create_new_version(
                    session, project_id, artifact_id, payload, user_id
                )
                await session.commit()
                return result

        @router.post("/{artifact_id}/finalize", response_model=Artifact)
        async def mark_as_final(
            artifact_id: UUID,
            request: Request,
        ):
            """Mark an artifact as final."""
            project_id = getattr(request.state, "project_id", None)
            user_id = getattr(request.state, "user_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            async with request.state.session as session:
                result = await self.service.mark_as_final(
                    session, project_id, artifact_id, user_id
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Artifact not found")
                await session.commit()
                return result
