"""
Agent Matrix - Interventions Data Access Object

CRUD operations for workflow interventions.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from oss.src.utils.logging import get_module_logger
from oss.src.dbs.postgres.shared.engine import engine

from extensions.interventions.dbes import InterventionDBE
from extensions.interventions.types import (
    Intervention,
    InterventionCreate,
    InterventionQuery,
    InterventionStatus,
)

log = get_module_logger(__name__)


class InterventionsDAO:
    """Data access object for interventions."""

    async def create_intervention(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: InterventionCreate,
    ) -> Intervention:
        """Create a new intervention."""
        async with engine.core_session() as session:
            dbe = InterventionDBE(
                project_id=project_id,
                created_by_id=user_id,
                workflow_id=dto.workflow_id,
                execution_id=dto.execution_id,
                step_id=dto.step_id,
                intervention_type=dto.intervention_type.value,
                message=dto.message,
                data=dto.data,
                status="pending",
            )
            session.add(dbe)
            await session.flush()
            return self._intervention_to_dto(dbe)

    async def get_intervention(
        self,
        *,
        project_id: UUID,
        intervention_id: UUID,
    ) -> Optional[Intervention]:
        """Get an intervention by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(InterventionDBE)
                .where(InterventionDBE.project_id == project_id)
                .where(InterventionDBE.id == intervention_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._intervention_to_dto(dbe) if dbe else None

    async def list_interventions(
        self,
        *,
        project_id: UUID,
        query: InterventionQuery,
    ) -> List[Intervention]:
        """List interventions with optional filtering."""
        async with engine.core_session() as session:
            stmt = select(InterventionDBE).where(
                InterventionDBE.project_id == project_id
            )

            if query.workflow_id:
                stmt = stmt.where(InterventionDBE.workflow_id == query.workflow_id)
            if query.execution_id:
                stmt = stmt.where(InterventionDBE.execution_id == query.execution_id)
            if query.intervention_type:
                stmt = stmt.where(
                    InterventionDBE.intervention_type == query.intervention_type.value
                )
            if query.status:
                stmt = stmt.where(InterventionDBE.status == query.status.value)

            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            stmt = stmt.order_by(InterventionDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._intervention_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_status(
        self,
        *,
        project_id: UUID,
        intervention_id: UUID,
        status: InterventionStatus,
    ) -> Optional[Intervention]:
        """Update intervention status."""
        async with engine.core_session() as session:
            stmt = (
                select(InterventionDBE)
                .where(InterventionDBE.project_id == project_id)
                .where(InterventionDBE.id == intervention_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            dbe.status = status.value
            await session.flush()
            return self._intervention_to_dto(dbe)

    async def get_pending_for_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> List[Intervention]:
        """Get all pending interventions for an execution."""
        async with engine.core_session() as session:
            stmt = (
                select(InterventionDBE)
                .where(InterventionDBE.project_id == project_id)
                .where(InterventionDBE.execution_id == execution_id)
                .where(InterventionDBE.status == "pending")
                .order_by(InterventionDBE.created_at.asc())
            )
            result = await session.execute(stmt)
            return [self._intervention_to_dto(dbe) for dbe in result.scalars().all()]

    def _intervention_to_dto(self, dbe: InterventionDBE) -> Intervention:
        """Convert InterventionDBE to Intervention DTO."""
        return Intervention(
            id=dbe.id,
            project_id=dbe.project_id,
            workflow_id=dbe.workflow_id,
            execution_id=dbe.execution_id,
            step_id=dbe.step_id,
            intervention_type=dbe.intervention_type,
            message=dbe.message,
            data=dbe.data,
            status=dbe.status,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )
