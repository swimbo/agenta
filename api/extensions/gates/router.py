"""
Agent Matrix - Gates Router

FastAPI router for gate endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from oss.src.utils.logging import get_module_logger
from oss.src.apis.fastapi.shared.utils import handle_exceptions
from oss.src.core.shared.dtos import ProjectScopeDTO

from extensions.gates.service import GatesService
from extensions.gates.types import (
    GateCreate,
    GateQuery,
    GateType,
    GateStatus,
    GateCreateRequest,
    GateResponse,
    GatesListResponse,
    GateApproveRequest,
    GateRejectRequest,
)

log = get_module_logger(__name__)


class GatesRouter:
    """Router for gate endpoints."""

    def __init__(self):
        self.service = GatesService()
        self.router = APIRouter(prefix="/gates", tags=["Gates"])
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("", response_model=GateResponse)
        @handle_exceptions
        async def create_gate(
            request: GateCreateRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Create a new gate."""
            dto = GateCreate(
                workflow_id=UUID(request.workflow_id),
                execution_id=UUID(request.execution_id),
                step_id=request.step_id,
                gate_type=GateType(request.gate_type),
                config=request.config,
                context=request.context,
            )

            gate = await self.service.create_gate(
                project_id=project_scope.project_id,
                user_id=project_scope.user_id,
                dto=dto,
            )
            return GateResponse.from_dto(gate)

        @self.router.get("", response_model=GatesListResponse)
        @handle_exceptions
        async def list_gates(
            project_scope: ProjectScopeDTO = Depends(),
            workflow_id: Optional[str] = Query(None),
            execution_id: Optional[str] = Query(None),
            gate_type: Optional[str] = Query(None),
            status: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=100),
        ):
            """List gates."""
            query = GateQuery(
                workflow_id=UUID(workflow_id) if workflow_id else None,
                execution_id=UUID(execution_id) if execution_id else None,
                gate_type=GateType(gate_type) if gate_type else None,
                status=GateStatus(status) if status else None,
                offset=offset,
                limit=limit,
            )
            gates = await self.service.list_gates(
                project_id=project_scope.project_id,
                query=query,
            )
            return GatesListResponse(
                gates=[GateResponse.from_dto(g) for g in gates],
                total=len(gates),
                offset=offset,
                limit=limit,
            )

        @self.router.get("/{gate_id}", response_model=GateResponse)
        @handle_exceptions
        async def get_gate(
            gate_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get a gate by ID."""
            gate = await self.service.get_gate(
                project_id=project_scope.project_id,
                gate_id=gate_id,
            )
            if not gate:
                raise HTTPException(status_code=404, detail="Gate not found")
            return GateResponse.from_dto(gate)

        @self.router.post("/{gate_id}/approve", response_model=GateResponse)
        @handle_exceptions
        async def approve_gate(
            gate_id: UUID,
            request: GateApproveRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Approve a gate."""
            gate = await self.service.approve_gate(
                project_id=project_scope.project_id,
                gate_id=gate_id,
                user_id=project_scope.user_id,
            )
            if not gate:
                raise HTTPException(status_code=404, detail="Gate not found")
            return GateResponse.from_dto(gate)

        @self.router.post("/{gate_id}/reject", response_model=GateResponse)
        @handle_exceptions
        async def reject_gate(
            gate_id: UUID,
            request: GateRejectRequest,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Reject a gate."""
            gate = await self.service.reject_gate(
                project_id=project_scope.project_id,
                gate_id=gate_id,
                user_id=project_scope.user_id,
                reason=request.reason,
            )
            if not gate:
                raise HTTPException(status_code=404, detail="Gate not found")
            return GateResponse.from_dto(gate)

        # Execution-specific endpoints
        @self.router.get("/executions/{execution_id}/pending")
        @handle_exceptions
        async def get_pending_gates(
            execution_id: UUID,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get pending gates for an execution."""
            gates = await self.service.get_pending_gates(
                project_id=project_scope.project_id,
                execution_id=execution_id,
            )
            return {
                "gates": [GateResponse.from_dto(g) for g in gates],
                "total": len(gates),
            }

        @self.router.get("/executions/{execution_id}/steps/{step_id}")
        @handle_exceptions
        async def get_gate_for_step(
            execution_id: UUID,
            step_id: str,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Get the gate for a specific step."""
            gate = await self.service.get_gate_for_step(
                project_id=project_scope.project_id,
                execution_id=execution_id,
                step_id=step_id,
            )
            if not gate:
                raise HTTPException(status_code=404, detail="Gate not found")
            return GateResponse.from_dto(gate)

        @self.router.get("/executions/{execution_id}/steps/{step_id}/approved")
        @handle_exceptions
        async def is_step_approved(
            execution_id: UUID,
            step_id: str,
            project_scope: ProjectScopeDTO = Depends(),
        ):
            """Check if a step is approved."""
            approved = await self.service.is_step_approved(
                project_id=project_scope.project_id,
                execution_id=execution_id,
                step_id=step_id,
            )
            return {"approved": approved}
