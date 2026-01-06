"""
Agent Matrix - Workflows Router

FastAPI router for workflow endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from oss.src.utils.logging import get_module_logger
from oss.src.apis.fastapi.shared.utils import handle_exceptions
from oss.src.core.shared.dtos import ProjectScopeDTO

from extensions.workflows.service import WorkflowsService
from extensions.workflows.types import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowQuery,
    WorkflowScope,
    WorkflowEnvironment,
    WorkflowExecutionStatus,
    WorkflowExecutionQuery,
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowResponse,
    WorkflowsListResponse,
    WorkflowExecutionResponse,
    WorkflowRunRequest,
    WorkflowStep,
)

log = get_module_logger(__name__)


class WorkflowsRouter:
    """Router for workflow endpoints."""

    def __init__(self):
        self.service = WorkflowsService()
        self.router = APIRouter(prefix="/workflows", tags=["Workflows"])
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("", response_model=WorkflowResponse)
        @handle_exceptions
        async def create_workflow(
            request: WorkflowCreateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Create a new workflow."""
            # Convert request to DTO
            steps = [
                WorkflowStep(
                    id=s.get("id", ""),
                    name=s.get("name", ""),
                    agent_id=s.get("agent_id"),
                    depends_on=s.get("depends_on", []),
                    config=s.get("config"),
                )
                for s in (request.steps or [])
            ]

            dto = WorkflowCreate(
                name=request.name,
                description=request.description,
                steps=steps,
                scope=WorkflowScope(request.scope) if request.scope else None,
                environment=WorkflowEnvironment(request.environment) if request.environment else None,
                tags=request.tags,
            )

            workflow = await self.service.create_workflow(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            return WorkflowResponse.from_dto(workflow)

        @self.router.get("", response_model=WorkflowsListResponse)
        @handle_exceptions
        async def list_workflows(
            project_scope: ProjectScopeDTO = Depends(),
            name: Optional[str] = Query(None),
            scope: Optional[str] = Query(None),
            environment: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=100),
        ):
            """List workflows."""
            query = WorkflowQuery(
                name=name,
                scope=WorkflowScope(scope) if scope else None,
                environment=WorkflowEnvironment(environment) if environment else None,
                offset=offset,
                limit=limit,
            )
            workflows = await self.service.list_workflows(
                project_id=project_scope.project_id,
                query=query,
            )
            return WorkflowsListResponse(
                workflows=[WorkflowResponse.from_dto(w) for w in workflows],
                total=len(workflows),
                offset=offset,
                limit=limit,
            )

        @self.router.get("/{workflow_id}", response_model=WorkflowResponse)
        @handle_exceptions
        async def get_workflow(
            workflow_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get a workflow by ID."""
            workflow = await self.service.get_workflow(
                project_id=project_scope.project_id,
                workflow_id=workflow_id,
            )
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return WorkflowResponse.from_dto(workflow)

        @self.router.patch("/{workflow_id}", response_model=WorkflowResponse)
        @handle_exceptions
        async def update_workflow(
            workflow_id: UUID,
            request: WorkflowUpdateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Update a workflow."""
            steps = None
            if request.steps is not None:
                steps = [
                    WorkflowStep(
                        id=s.get("id", ""),
                        name=s.get("name", ""),
                        agent_id=s.get("agent_id"),
                        depends_on=s.get("depends_on", []),
                        config=s.get("config"),
                    )
                    for s in request.steps
                ]

            dto = WorkflowUpdate(
                name=request.name,
                description=request.description,
                steps=steps,
                scope=WorkflowScope(request.scope) if request.scope else None,
                environment=WorkflowEnvironment(request.environment) if request.environment else None,
                tags=request.tags,
            )

            workflow = await self.service.update_workflow(
                project_id=project_scope.project_id,
                workflow_id=workflow_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return WorkflowResponse.from_dto(workflow)

        @self.router.delete("/{workflow_id}")
        @handle_exceptions
        async def delete_workflow(
            workflow_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Delete a workflow."""
            deleted = await self.service.delete_workflow(
                project_id=project_scope.project_id,
                workflow_id=workflow_id,
                user_id=project_scope.user_id,
            )
            if not deleted:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return {"success": True}

        # Execution endpoints
        @self.router.post("/{workflow_id}/run", response_model=WorkflowExecutionResponse)
        @handle_exceptions
        async def run_workflow(
            workflow_id: UUID,
            request: WorkflowRunRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Start a workflow execution."""
            execution = await self.service.run_workflow(
                project_id=project_scope.project_id,
                workflow_id=workflow_id,
                user_id=project_scope.user_id,
                input=request.input,
            )
            return WorkflowExecutionResponse.from_dto(execution)

        @self.router.get("/{workflow_id}/executions")
        @handle_exceptions
        async def list_executions(
            workflow_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
            status: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=100),
        ):
            """List workflow executions."""
            query = WorkflowExecutionQuery(
                workflow_id=workflow_id,
                status=WorkflowExecutionStatus(status) if status else None,
                offset=offset,
                limit=limit,
            )
            executions = await self.service.list_executions(
                project_id=project_scope.project_id,
                query=query,
            )
            return {
                "executions": [WorkflowExecutionResponse.from_dto(e) for e in executions],
                "total": len(executions),
                "offset": offset,
                "limit": limit,
            }

        @self.router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
        @handle_exceptions
        async def get_execution(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get a workflow execution by ID."""
            execution = await self.service.get_execution(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")
            return WorkflowExecutionResponse.from_dto(execution)

        @self.router.post("/executions/{execution_id}/pause")
        @handle_exceptions
        async def pause_execution(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Pause a workflow execution."""
            execution = await self.service.pause_execution(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")
            return WorkflowExecutionResponse.from_dto(execution)

        @self.router.post("/executions/{execution_id}/resume")
        @handle_exceptions
        async def resume_execution(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Resume a paused workflow execution."""
            execution = await self.service.resume_execution(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")
            return WorkflowExecutionResponse.from_dto(execution)

        @self.router.post("/executions/{execution_id}/cancel")
        @handle_exceptions
        async def cancel_execution(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Cancel a workflow execution."""
            execution = await self.service.cancel_execution(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")
            return WorkflowExecutionResponse.from_dto(execution)
