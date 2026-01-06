"""
Agent Matrix - Workflows Data Access Object

CRUD operations for workflows and executions.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from oss.src.utils.logging import get_module_logger
from oss.src.dbs.postgres.shared.engine import engine

from extensions.workflows.dbes import (
    WorkflowDBE,
    WorkflowExecutionDBE,
    WorkflowCostDBE,
)
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


class WorkflowsDAO:
    """Data access object for workflows and executions."""

    # -------------------------------------------------------------------------
    # Workflows CRUD
    # -------------------------------------------------------------------------

    async def create_workflow(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: WorkflowCreate,
    ) -> Workflow:
        """Create a new workflow."""
        async with engine.core_session() as session:
            # Convert steps to dict format
            steps_data = [
                {
                    "id": step.id,
                    "name": step.name,
                    "agent_id": str(step.agent_id) if step.agent_id else None,
                    "depends_on": step.depends_on,
                    "config": step.config,
                }
                for step in dto.steps
            ] if dto.steps else []

            dbe = WorkflowDBE(
                project_id=project_id,
                created_by_id=user_id,
                name=dto.name,
                description=dto.description,
                steps=steps_data,
                scope=dto.scope.value if dto.scope else "personal",
                environment=dto.environment.value if dto.environment else "dev",
                tags=dto.tags,
                meta=dto.meta,
            )
            session.add(dbe)
            await session.flush()
            return self._workflow_to_dto(dbe)

    async def get_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
    ) -> Optional[Workflow]:
        """Get a workflow by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowDBE)
                .where(WorkflowDBE.project_id == project_id)
                .where(WorkflowDBE.id == workflow_id)
                .where(WorkflowDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._workflow_to_dto(dbe) if dbe else None

    async def list_workflows(
        self,
        *,
        project_id: UUID,
        query: WorkflowQuery,
    ) -> List[Workflow]:
        """List workflows with optional filtering."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowDBE)
                .where(WorkflowDBE.project_id == project_id)
                .where(WorkflowDBE.deleted_at.is_(None))
            )

            if query.scope:
                stmt = stmt.where(WorkflowDBE.scope == query.scope.value)
            if query.environment:
                stmt = stmt.where(WorkflowDBE.environment == query.environment.value)
            if query.name:
                stmt = stmt.where(WorkflowDBE.name.ilike(f"%{query.name}%"))

            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            stmt = stmt.order_by(WorkflowDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._workflow_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        dto: WorkflowUpdate,
    ) -> Optional[Workflow]:
        """Update a workflow."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowDBE)
                .where(WorkflowDBE.project_id == project_id)
                .where(WorkflowDBE.id == workflow_id)
                .where(WorkflowDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            if dto.name is not None:
                dbe.name = dto.name
            if dto.description is not None:
                dbe.description = dto.description
            if dto.steps is not None:
                steps_data = [
                    {
                        "id": step.id,
                        "name": step.name,
                        "agent_id": str(step.agent_id) if step.agent_id else None,
                        "depends_on": step.depends_on,
                        "config": step.config,
                    }
                    for step in dto.steps
                ]
                dbe.steps = steps_data
            if dto.scope is not None:
                dbe.scope = dto.scope.value
            if dto.environment is not None:
                dbe.environment = dto.environment.value
            if dto.tags is not None:
                dbe.tags = dto.tags
            if dto.meta is not None:
                dbe.meta = dto.meta

            dbe.updated_by_id = user_id
            await session.flush()
            return self._workflow_to_dto(dbe)

    async def delete_workflow(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a workflow."""
        async with engine.core_session() as session:
            stmt = (
                update(WorkflowDBE)
                .where(WorkflowDBE.project_id == project_id)
                .where(WorkflowDBE.id == workflow_id)
                .where(WorkflowDBE.deleted_at.is_(None))
                .values(
                    deleted_at=func.now(),
                    deleted_by_id=user_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    # -------------------------------------------------------------------------
    # Workflow Executions
    # -------------------------------------------------------------------------

    async def create_execution(
        self,
        *,
        project_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        dto: WorkflowExecutionCreate,
    ) -> WorkflowExecution:
        """Create a new workflow execution."""
        async with engine.core_session() as session:
            dbe = WorkflowExecutionDBE(
                project_id=project_id,
                workflow_id=workflow_id,
                created_by_id=user_id,
                status="pending",
                input=dto.input,
                step_results={},
            )
            session.add(dbe)
            await session.flush()
            return self._execution_to_dto(dbe)

    async def get_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowExecutionDBE)
                .where(WorkflowExecutionDBE.project_id == project_id)
                .where(WorkflowExecutionDBE.id == execution_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._execution_to_dto(dbe) if dbe else None

    async def list_executions(
        self,
        *,
        project_id: UUID,
        query: WorkflowExecutionQuery,
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filtering."""
        async with engine.core_session() as session:
            stmt = select(WorkflowExecutionDBE).where(
                WorkflowExecutionDBE.project_id == project_id
            )

            if query.workflow_id:
                stmt = stmt.where(
                    WorkflowExecutionDBE.workflow_id == query.workflow_id
                )
            if query.status:
                stmt = stmt.where(
                    WorkflowExecutionDBE.status == query.status.value
                )

            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            stmt = stmt.order_by(WorkflowExecutionDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._execution_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_execution_status(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
        status: str,
        current_step_id: Optional[str] = None,
        output: Optional[str] = None,
    ) -> Optional[WorkflowExecution]:
        """Update execution status."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowExecutionDBE)
                .where(WorkflowExecutionDBE.project_id == project_id)
                .where(WorkflowExecutionDBE.id == execution_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            dbe.status = status
            if current_step_id is not None:
                dbe.current_step_id = current_step_id
            if output is not None:
                dbe.output = output

            # Set timing
            now = datetime.now(timezone.utc)
            if status == "running" and dbe.started_at is None:
                dbe.started_at = now
            if status in ("completed", "failed", "cancelled"):
                dbe.completed_at = now

            await session.flush()
            return self._execution_to_dto(dbe)

    async def update_step_result(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
        step_id: str,
        result: dict,
    ) -> Optional[WorkflowExecution]:
        """Update step result in execution."""
        async with engine.core_session() as session:
            stmt = (
                select(WorkflowExecutionDBE)
                .where(WorkflowExecutionDBE.project_id == project_id)
                .where(WorkflowExecutionDBE.id == execution_id)
            )
            db_result = await session.execute(stmt)
            dbe = db_result.scalars().first()

            if not dbe:
                return None

            step_results = dict(dbe.step_results or {})
            step_results[step_id] = result
            dbe.step_results = step_results

            await session.flush()
            return self._execution_to_dto(dbe)

    # -------------------------------------------------------------------------
    # DTO Mappings
    # -------------------------------------------------------------------------

    def _workflow_to_dto(self, dbe: WorkflowDBE) -> Workflow:
        """Convert WorkflowDBE to Workflow DTO."""
        return Workflow(
            id=dbe.id,
            project_id=dbe.project_id,
            name=dbe.name,
            description=dbe.description,
            steps=dbe.steps or [],
            scope=dbe.scope,
            environment=dbe.environment,
            version=dbe.version,
            tags=dbe.tags,
            meta=dbe.meta,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )

    def _execution_to_dto(self, dbe: WorkflowExecutionDBE) -> WorkflowExecution:
        """Convert WorkflowExecutionDBE to WorkflowExecution DTO."""
        return WorkflowExecution(
            id=dbe.id,
            project_id=dbe.project_id,
            workflow_id=dbe.workflow_id,
            status=dbe.status,
            current_step_id=dbe.current_step_id,
            step_results=dbe.step_results or {},
            input=dbe.input,
            output=dbe.output,
            started_at=dbe.started_at,
            completed_at=dbe.completed_at,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
        )
