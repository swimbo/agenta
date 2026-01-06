"""
Agent Matrix - Overnight Runs Service

Business logic for overnight run operations including batch execution.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from extensions.overnights.dao import OvernightsDAO
from extensions.overnights.types import (
    OvernightRunCreate,
    OvernightRunUpdate,
    OvernightRun,
    OvernightRunProgress,
    WorkflowResult,
)


class OvernightsService:
    """Service for overnight run operations."""

    def __init__(self, dao: OvernightsDAO, workflows_service=None):
        self.dao = dao
        self.workflows_service = workflows_service

    async def create_overnight_run(
        self,
        session,
        project_id: UUID,
        dto: OvernightRunCreate,
        created_by_id: Optional[UUID] = None,
    ) -> OvernightRun:
        """Create a new overnight run."""
        return await self.dao.create(session, project_id, dto, created_by_id)

    async def get_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Get an overnight run by ID."""
        return await self.dao.get(session, project_id, run_id)

    async def list_overnight_runs(
        self,
        session,
        project_id: UUID,
        status: Optional[str] = None,
        scheduled_after: Optional[datetime] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OvernightRun]:
        """List overnight runs with optional filters."""
        return await self.dao.list(
            session,
            project_id,
            status,
            scheduled_after,
            scheduled_before,
            limit,
            offset,
        )

    async def update_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
        dto: OvernightRunUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[OvernightRun]:
        """Update an overnight run."""
        return await self.dao.update(
            session, project_id, run_id, dto, updated_by_id
        )

    async def delete_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Delete an overnight run."""
        return await self.dao.delete(
            session, project_id, run_id, deleted_by_id
        )

    async def start_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Start an overnight run."""
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            return None

        if run.status != "scheduled":
            raise ValueError(f"Cannot start run in status: {run.status}")

        return await self.dao.update_status(
            session, project_id, run_id, "running"
        )

    async def pause_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Pause an overnight run."""
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            return None

        if run.status != "running":
            raise ValueError(f"Cannot pause run in status: {run.status}")

        return await self.dao.update_status(
            session, project_id, run_id, "paused"
        )

    async def resume_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Resume a paused overnight run."""
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            return None

        if run.status != "paused":
            raise ValueError(f"Cannot resume run in status: {run.status}")

        return await self.dao.update_status(
            session, project_id, run_id, "running"
        )

    async def cancel_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Cancel an overnight run."""
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            return None

        if run.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot cancel run in status: {run.status}")

        return await self.dao.update_status(
            session, project_id, run_id, "cancelled"
        )

    async def get_progress(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRunProgress]:
        """Get progress information for an overnight run."""
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            return None

        total = len(run.workflow_ids)
        completed = len([r for r in run.workflow_results if r.status == "completed"])
        failed = len([r for r in run.workflow_results if r.status == "failed"])

        current_workflow_id = None
        if run.current_workflow_index < total:
            current_workflow_id = run.workflow_ids[run.current_workflow_index]

        progress_percent = (completed + failed) / total * 100 if total > 0 else 0

        # Estimate remaining time based on average duration
        estimated_remaining_ms = None
        if run.workflow_results:
            avg_duration = sum(r.duration_ms for r in run.workflow_results) / len(run.workflow_results)
            remaining_count = total - (completed + failed)
            estimated_remaining_ms = int(avg_duration * remaining_count)

        return OvernightRunProgress(
            id=run.id,
            status=run.status,
            total_workflows=total,
            completed_workflows=completed,
            failed_workflows=failed,
            current_workflow_index=run.current_workflow_index,
            current_workflow_id=current_workflow_id,
            progress_percent=progress_percent,
            estimated_remaining_ms=estimated_remaining_ms,
        )

    async def execute_overnight_run(
        self,
        session,
        project_id: UUID,
        run_id: UUID,
    ) -> OvernightRun:
        """
        Execute an overnight run (batch workflow execution).

        This is the main execution loop that runs each workflow sequentially.
        """
        run = await self.dao.get(session, project_id, run_id)
        if not run:
            raise ValueError("Overnight run not found")

        if not self.workflows_service:
            raise RuntimeError("Workflows service not configured")

        # Start the run
        run = await self.dao.update_status(session, project_id, run_id, "running")
        await session.commit()

        workflow_results = list(run.workflow_results)
        total_tokens_input = run.total_tokens_input
        total_tokens_output = run.total_tokens_output
        total_cost = float(run.total_cost)

        # Execute each workflow starting from current index
        for i, workflow_id in enumerate(run.workflow_ids[run.current_workflow_index:], start=run.current_workflow_index):
            # Check for pause/cancel
            run = await self.dao.get(session, project_id, run_id)
            if run.status in ("paused", "cancelled"):
                break

            # Update current index
            await self.dao.update_status(
                session, project_id, run_id, "running",
                current_workflow_index=i,
            )
            await session.commit()

            start_time = datetime.utcnow()
            try:
                # Execute workflow
                result = await self.workflows_service.execute_workflow(
                    session, project_id, workflow_id
                )

                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                workflow_results.append(WorkflowResult(
                    workflow_id=workflow_id,
                    status="completed",
                    output=result.output if hasattr(result, 'output') else None,
                    tokens_input=result.tokens_input if hasattr(result, 'tokens_input') else 0,
                    tokens_output=result.tokens_output if hasattr(result, 'tokens_output') else 0,
                    cost=float(result.cost) if hasattr(result, 'cost') else 0.0,
                    duration_ms=duration_ms,
                ))

                # Update totals
                if hasattr(result, 'tokens_input'):
                    total_tokens_input += result.tokens_input
                if hasattr(result, 'tokens_output'):
                    total_tokens_output += result.tokens_output
                if hasattr(result, 'cost'):
                    total_cost += float(result.cost)

            except Exception as e:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                workflow_results.append(WorkflowResult(
                    workflow_id=workflow_id,
                    status="failed",
                    error=str(e),
                    duration_ms=duration_ms,
                ))

            # Update results
            await self.dao.update_status(
                session, project_id, run_id, "running",
                workflow_results=[r.model_dump() for r in workflow_results],
                total_tokens_input=total_tokens_input,
                total_tokens_output=total_tokens_output,
                total_cost=total_cost,
            )
            await session.commit()

        # Determine final status
        run = await self.dao.get(session, project_id, run_id)
        if run.status == "running":
            # Check if all completed
            failed_count = len([r for r in workflow_results if r.status == "failed"])
            final_status = "completed" if failed_count == 0 else "failed"

            run = await self.dao.update_status(
                session, project_id, run_id, final_status
            )
            await session.commit()

        return run
