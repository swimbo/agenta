"""
Agent Matrix - Interventions Service

Business logic for human-in-the-loop interventions.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from oss.src.utils.logging import get_module_logger

from extensions.interventions.dao import InterventionsDAO
from extensions.interventions.types import (
    Intervention,
    InterventionCreate,
    InterventionQuery,
    InterventionType,
    InterventionStatus,
)

log = get_module_logger(__name__)


class InterventionsService:
    """Service for intervention operations."""

    def __init__(self):
        self.dao = InterventionsDAO()

    # -------------------------------------------------------------------------
    # Core CRUD
    # -------------------------------------------------------------------------

    async def create_intervention(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: InterventionCreate,
    ) -> Intervention:
        """Create a new intervention."""
        log.info(
            f"Creating {dto.intervention_type} intervention "
            f"for execution {dto.execution_id}"
        )
        intervention = await self.dao.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=dto,
        )

        # TODO: Notify Bridge about the intervention
        # Bridge will handle applying the intervention to the running execution

        return intervention

    async def get_intervention(
        self,
        *,
        project_id: UUID,
        intervention_id: UUID,
    ) -> Optional[Intervention]:
        """Get an intervention by ID."""
        return await self.dao.get_intervention(
            project_id=project_id,
            intervention_id=intervention_id,
        )

    async def list_interventions(
        self,
        *,
        project_id: UUID,
        query: InterventionQuery,
    ) -> List[Intervention]:
        """List interventions with optional filtering."""
        return await self.dao.list_interventions(
            project_id=project_id,
            query=query,
        )

    async def mark_applied(
        self,
        *,
        project_id: UUID,
        intervention_id: UUID,
    ) -> Optional[Intervention]:
        """Mark an intervention as applied."""
        log.info(f"Marking intervention {intervention_id} as applied")
        return await self.dao.update_status(
            project_id=project_id,
            intervention_id=intervention_id,
            status=InterventionStatus.APPLIED,
        )

    async def mark_failed(
        self,
        *,
        project_id: UUID,
        intervention_id: UUID,
    ) -> Optional[Intervention]:
        """Mark an intervention as failed."""
        log.info(f"Marking intervention {intervention_id} as failed")
        return await self.dao.update_status(
            project_id=project_id,
            intervention_id=intervention_id,
            status=InterventionStatus.FAILED,
        )

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    async def pause_execution(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        message: Optional[str] = None,
    ) -> Intervention:
        """Pause a workflow execution."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                intervention_type=InterventionType.PAUSE,
                message=message,
            ),
        )

    async def resume_execution(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        message: Optional[str] = None,
    ) -> Intervention:
        """Resume a paused workflow execution."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                intervention_type=InterventionType.RESUME,
                message=message,
            ),
        )

    async def inject_data(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        data: Dict[str, Any],
        step_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Intervention:
        """Inject data into a workflow execution."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                intervention_type=InterventionType.INJECT,
                message=message,
                data=data,
            ),
        )

    async def approve_step(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        step_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Intervention:
        """Approve a step or gate."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                intervention_type=InterventionType.APPROVE,
                message=message,
            ),
        )

    async def reject_step(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        reason: str,
        step_id: Optional[str] = None,
    ) -> Intervention:
        """Reject a step or gate."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                step_id=step_id,
                intervention_type=InterventionType.REJECT,
                message=reason,
            ),
        )

    async def cancel_execution(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        workflow_id: UUID,
        execution_id: UUID,
        message: Optional[str] = None,
    ) -> Intervention:
        """Cancel a workflow execution."""
        return await self.create_intervention(
            project_id=project_id,
            user_id=user_id,
            dto=InterventionCreate(
                workflow_id=workflow_id,
                execution_id=execution_id,
                intervention_type=InterventionType.CANCEL,
                message=message,
            ),
        )

    async def get_pending_interventions(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> List[Intervention]:
        """Get pending interventions for an execution."""
        return await self.dao.get_pending_for_execution(
            project_id=project_id,
            execution_id=execution_id,
        )
