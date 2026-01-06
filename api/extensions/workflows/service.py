"""
Agent Matrix - Workflows Service

Business logic for workflow management and execution.
"""

from typing import Optional, List
from uuid import UUID

from oss.src.utils.logging import get_module_logger

from extensions.workflows.dao import WorkflowsDAO
from extensions.workflows.types import (
    Workflow,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowQuery,
    WorkflowExecution,
    WorkflowExecutionCreate,
    WorkflowExecutionQuery,
)

log = get_module_logger(__name__)


class WorkflowsService:
    """Service for workflow operations."""

    def __init__(self):
        self.dao = WorkflowsDAO()

    # -------------------------------------------------------------------------
    # Workflow CRUD
    # -------------------------------------------------------------------------

    async def create_workflow(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: WorkflowCreate,
    ) -> Workflow:
        """Create a new workflow."""
        log.info(f"Creating workflow: {dto.name} for project {project_id}")
        return await self.dao.create_workflow(
            project_id=project_id,
            user_id=user_id,
            dto=dto,
        )

    async def get_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
    ) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return await self.dao.get_workflow(
            project_id=project_id,
            workflow_id=workflow_id,
        )

    async def list_workflows(
        self,
        *,
        project_id: UUID,
        query: WorkflowQuery,
    ) -> List[Workflow]:
        """List workflows with optional filtering."""
        return await self.dao.list_workflows(
            project_id=project_id,
            query=query,
        )

    async def update_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        dto: WorkflowUpdate,
    ) -> Optional[Workflow]:
        """Update a workflow."""
        log.info(f"Updating workflow {workflow_id}")
        return await self.dao.update_workflow(
            project_id=project_id,
            workflow_id=workflow_id,
            user_id=user_id,
            dto=dto,
        )

    async def delete_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a workflow."""
        log.info(f"Deleting workflow {workflow_id}")
        return await self.dao.delete_workflow(
            project_id=project_id,
            workflow_id=workflow_id,
            user_id=user_id,
        )

    # -------------------------------------------------------------------------
    # Workflow Execution
    # -------------------------------------------------------------------------

    async def run_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        input: Optional[str] = None,
    ) -> WorkflowExecution:
        """
        Start a workflow execution.

        This creates an execution record and initiates processing.
        The actual execution is handled by the Bridge integration.
        """
        log.info(f"Starting workflow execution for workflow {workflow_id}")

        # Create execution record
        execution = await self.dao.create_execution(
            project_id=project_id,
            workflow_id=workflow_id,
            user_id=user_id,
            dto=WorkflowExecutionCreate(input=input),
        )

        # TODO: Trigger Bridge to start execution
        # Bridge will handle the actual step-by-step execution
        # and update status via update_execution_status

        return execution

    async def get_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        return await self.dao.get_execution(
            project_id=project_id,
            execution_id=execution_id,
        )

    async def list_executions(
        self,
        *,
        project_id: UUID,
        query: WorkflowExecutionQuery,
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filtering."""
        return await self.dao.list_executions(
            project_id=project_id,
            query=query,
        )

    async def pause_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> Optional[WorkflowExecution]:
        """Pause a running workflow execution."""
        log.info(f"Pausing execution {execution_id}")
        return await self.dao.update_execution_status(
            project_id=project_id,
            execution_id=execution_id,
            status="paused",
        )

    async def resume_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> Optional[WorkflowExecution]:
        """Resume a paused workflow execution."""
        log.info(f"Resuming execution {execution_id}")
        # TODO: Trigger Bridge to resume execution
        return await self.dao.update_execution_status(
            project_id=project_id,
            execution_id=execution_id,
            status="running",
        )

    async def cancel_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> Optional[WorkflowExecution]:
        """Cancel a workflow execution."""
        log.info(f"Cancelling execution {execution_id}")
        return await self.dao.update_execution_status(
            project_id=project_id,
            execution_id=execution_id,
            status="cancelled",
        )
