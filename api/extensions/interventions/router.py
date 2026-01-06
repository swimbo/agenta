"""
Agent Matrix - Interventions Router

FastAPI router for intervention endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from oss.src.utils.logging import get_module_logger
from oss.src.apis.fastapi.shared.utils import handle_exceptions
from oss.src.core.shared.dtos import ProjectScopeDTO

from extensions.interventions.service import InterventionsService
from extensions.interventions.types import (
    InterventionCreate,
    InterventionQuery,
    InterventionType,
    InterventionStatus,
    InterventionCreateRequest,
    InterventionResponse,
    InterventionsListResponse,
    PauseRequest,
    ResumeRequest,
    InjectRequest,
    ApproveRequest,
    RejectRequest,
)

log = get_module_logger(__name__)


class InterventionsRouter:
    """Router for intervention endpoints."""

    def __init__(self):
        self.service = InterventionsService()
        self.router = APIRouter(prefix="/interventions", tags=["Interventions"])
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("", response_model=InterventionResponse)
        @handle_exceptions
        async def create_intervention(
            request: InterventionCreateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Create a new intervention."""
            dto = InterventionCreate(
                workflow_id=UUID(request.workflow_id),
                execution_id=UUID(request.execution_id),
                step_id=request.step_id,
                intervention_type=InterventionType(request.intervention_type),
                message=request.message,
                data=request.data,
            )

            intervention = await self.service.create_intervention(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.get("", response_model=InterventionsListResponse)
        @handle_exceptions
        async def list_interventions(
            project_scope: ProjectScopeDTO = Depends(),
            workflow_id: Optional[str] = Query(None),
            execution_id: Optional[str] = Query(None),
            intervention_type: Optional[str] = Query(None),
            status: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=100),
        ):
            """List interventions."""
            query = InterventionQuery(
                workflow_id=UUID(workflow_id) if workflow_id else None,
                execution_id=UUID(execution_id) if execution_id else None,
                intervention_type=InterventionType(intervention_type) if intervention_type else None,
                status=InterventionStatus(status) if status else None,
                offset=offset,
                limit=limit,
            )
            interventions = await self.service.list_interventions(
                project_id=project_scope.project_id,
                query=query,
            )
            return InterventionsListResponse(
                interventions=[InterventionResponse.from_dto(i) for i in interventions],
                total=len(interventions),
                offset=offset,
                limit=limit,
            )

        @self.router.get("/{intervention_id}", response_model=InterventionResponse)
        @handle_exceptions
        async def get_intervention(
            intervention_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get an intervention by ID."""
            intervention = await self.service.get_intervention(
                project_id=project_scope.project_id,
                intervention_id=intervention_id,
            )
            if not intervention:
                raise HTTPException(status_code=404, detail="Intervention not found")
            return InterventionResponse.from_dto(intervention)

        # Convenience endpoints for specific execution
        @self.router.post("/executions/{execution_id}/pause", response_model=InterventionResponse)
        @handle_exceptions
        async def pause_execution(
            execution_id: UUID,
            request: PauseRequest,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Pause a workflow execution."""
            intervention = await self.service.pause_execution(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
                message=request.message,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.post("/executions/{execution_id}/resume", response_model=InterventionResponse)
        @handle_exceptions
        async def resume_execution(
            execution_id: UUID,
            request: ResumeRequest,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Resume a paused execution."""
            intervention = await self.service.resume_execution(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
                message=request.message,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.post("/executions/{execution_id}/inject", response_model=InterventionResponse)
        @handle_exceptions
        async def inject_data(
            execution_id: UUID,
            request: InjectRequest,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Inject data into an execution."""
            intervention = await self.service.inject_data(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
                data=request.data,
                step_id=request.step_id,
                message=request.message,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.post("/executions/{execution_id}/approve", response_model=InterventionResponse)
        @handle_exceptions
        async def approve_step(
            execution_id: UUID,
            request: ApproveRequest,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Approve a step or gate."""
            intervention = await self.service.approve_step(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
                step_id=request.step_id,
                message=request.message,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.post("/executions/{execution_id}/reject", response_model=InterventionResponse)
        @handle_exceptions
        async def reject_step(
            execution_id: UUID,
            request: RejectRequest,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Reject a step or gate."""
            intervention = await self.service.reject_step(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
                reason=request.reason,
                step_id=request.step_id,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.post("/executions/{execution_id}/cancel", response_model=InterventionResponse)
        @handle_exceptions
        async def cancel_execution(
            execution_id: UUID,
            workflow_id: str = Query(...),
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Cancel an execution."""
            intervention = await self.service.cancel_execution(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                workflow_id=UUID(workflow_id),
                execution_id=execution_id,
            )
            return InterventionResponse.from_dto(intervention)

        @self.router.get("/executions/{execution_id}/pending")
        @handle_exceptions
        async def get_pending_interventions(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get pending interventions for an execution."""
            interventions = await self.service.get_pending_interventions(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            return {
                "interventions": [InterventionResponse.from_dto(i) for i in interventions],
                "total": len(interventions),
            }
