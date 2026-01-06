"""
Agent Matrix - Gates Service

Business logic for workflow approval gates.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from oss.src.utils.logging import get_module_logger

from extensions.gates.dao import GatesDAO
from extensions.gates.types import (
    Gate,
    GateCreate,
    GateQuery,
    GateType,
    GateStatus,
)

log = get_module_logger(__name__)


class GatesService:
    """Service for gate operations."""

    def __init__(self):
        self.dao = GatesDAO()

    # -------------------------------------------------------------------------
    # Core CRUD
    # -------------------------------------------------------------------------

    async def create_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: GateCreate,
    ) -> Gate:
        """Create a new gate."""
        log.info(
            f"Creating {dto.gate_type} gate for step {dto.step_id} "
            f"in execution {dto.execution_id}"
        )
        return await self.dao.create_gate(
            project_id=project_id,
            user_id=user_id,
            dto=dto,
        )

    async def get_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
    ) -> Optional[Gate]:
        """Get a gate by ID."""
        return await self.dao.get_gate(
            project_id=project_id,
            gate_id=gate_id,
        )

    async def list_gates(
        self,
        *,
        project_id: UUID,
        query: GateQuery,
    ) -> List[Gate]:
        """List gates with optional filtering."""
        return await self.dao.list_gates(
            project_id=project_id,
            query=query,
        )

    async def approve_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        user_id: UUID,
    ) -> Optional[Gate]:
        """Approve a gate."""
        log.info(f"Approving gate {gate_id} by user {user_id}")
        gate = await self.dao.approve_gate(
            project_id=project_id,
            gate_id=gate_id,
            user_id=user_id,
        )

        if gate:
            # TODO: Notify Bridge that gate is approved
            # Bridge will resume execution
            pass

        return gate

    async def reject_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> Optional[Gate]:
        """Reject a gate."""
        log.info(f"Rejecting gate {gate_id} by user {user_id}: {reason}")
        gate = await self.dao.reject_gate(
            project_id=project_id,
            gate_id=gate_id,
            user_id=user_id,
            reason=reason,
        )

        if gate:
            # TODO: Notify Bridge that gate is rejected
            # Bridge will handle execution failure
            pass

        return gate

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    async def create_approval_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        step_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Gate:
        """Create an approval gate."""
        return await self.create_gate(
            project_id=project_id,
            user_id=user_id,
            dto=GateCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                gate_type=GateType.APPROVAL,
                context=context,
            ),
        )

    async def create_review_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        step_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Gate:
        """Create a review gate."""
        return await self.create_gate(
            project_id=project_id,
            user_id=user_id,
            dto=GateCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                gate_type=GateType.REVIEW,
                context=context,
            ),
        )

    async def create_deploy_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        step_id: str,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Gate:
        """Create a deploy gate."""
        return await self.create_gate(
            project_id=project_id,
            user_id=user_id,
            dto=GateCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                gate_type=GateType.DEPLOY,
                config=config,
                context=context,
            ),
        )

    async def create_cost_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        step_id: str,
        threshold: float,
        current_cost: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Gate:
        """Create a cost gate (triggers when cost exceeds threshold)."""
        return await self.create_gate(
            project_id=project_id,
            user_id=user_id,
            dto=GateCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                gate_type=GateType.COST,
                config={"threshold": threshold, "current_cost": current_cost},
                context=context,
            ),
        )

    async def get_pending_gates(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> List[Gate]:
        """Get all pending gates for an execution."""
        return await self.dao.get_pending_for_execution(
            project_id=project_id,
            execution_id=execution_id,
        )

    async def get_gate_for_step(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
        step_id: str,
    ) -> Optional[Gate]:
        """Get the gate for a specific step."""
        return await self.dao.get_gate_for_step(
            project_id=project_id,
            execution_id=execution_id,
            step_id=step_id,
        )

    async def is_step_approved(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
        step_id: str,
    ) -> bool:
        """Check if a step's gate is approved."""
        gate = await self.get_gate_for_step(
            project_id=project_id,
            execution_id=execution_id,
            step_id=step_id,
        )
        return gate is not None and gate.status == "approved"
