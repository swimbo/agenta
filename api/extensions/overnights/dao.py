"""
Agent Matrix - Overnight Runs DAO

Data access layer for overnight runs.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid_utils.compat as uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from extensions.overnights.dbes import OvernightRunDBE
from extensions.overnights.types import (
    OvernightRunCreate,
    OvernightRunUpdate,
    OvernightRun,
    WorkflowResult,
)


class OvernightsDAO:
    """Data access for overnight runs."""

    async def create(
        self,
        session: AsyncSession,
        project_id: UUID,
        dto: OvernightRunCreate,
        created_by_id: Optional[UUID] = None,
    ) -> OvernightRun:
        """Create a new overnight run."""
        dbe = OvernightRunDBE(
            id=uuid.uuid7(),
            project_id=project_id,
            name=dto.name,
            description=dto.description,
            workflow_ids=[str(wid) for wid in dto.workflow_ids],
            status="scheduled",
            scheduled_for=dto.scheduled_for,
            config=dto.config.model_dump() if dto.config else None,
            tags=dto.tags,
            created_by_id=created_by_id,
        )
        session.add(dbe)
        await session.flush()
        return self._to_dto(dbe)

    async def get(
        self,
        session: AsyncSession,
        project_id: UUID,
        run_id: UUID,
    ) -> Optional[OvernightRun]:
        """Get an overnight run by ID."""
        query = select(OvernightRunDBE).where(
            and_(
                OvernightRunDBE.project_id == project_id,
                OvernightRunDBE.id == run_id,
                OvernightRunDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        return self._to_dto(dbe) if dbe else None

    async def list(
        self,
        session: AsyncSession,
        project_id: UUID,
        status: Optional[str] = None,
        scheduled_after: Optional[datetime] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OvernightRun]:
        """List overnight runs with optional filters."""
        query = select(OvernightRunDBE).where(
            and_(
                OvernightRunDBE.project_id == project_id,
                OvernightRunDBE.deleted_at.is_(None),
            )
        )

        if status:
            query = query.where(OvernightRunDBE.status == status)
        if scheduled_after:
            query = query.where(OvernightRunDBE.scheduled_for >= scheduled_after)
        if scheduled_before:
            query = query.where(OvernightRunDBE.scheduled_for <= scheduled_before)

        query = query.order_by(OvernightRunDBE.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        return [self._to_dto(dbe) for dbe in result.scalars()]

    async def update(
        self,
        session: AsyncSession,
        project_id: UUID,
        run_id: UUID,
        dto: OvernightRunUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[OvernightRun]:
        """Update an overnight run."""
        query = select(OvernightRunDBE).where(
            and_(
                OvernightRunDBE.project_id == project_id,
                OvernightRunDBE.id == run_id,
                OvernightRunDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return None

        if dto.name is not None:
            dbe.name = dto.name
        if dto.description is not None:
            dbe.description = dto.description
        if dto.workflow_ids is not None:
            dbe.workflow_ids = [str(wid) for wid in dto.workflow_ids]
        if dto.scheduled_for is not None:
            dbe.scheduled_for = dto.scheduled_for
        if dto.config is not None:
            dbe.config = dto.config.model_dump()
        if dto.tags is not None:
            dbe.tags = dto.tags

        dbe.updated_at = datetime.utcnow()
        dbe.updated_by_id = updated_by_id

        await session.flush()
        return self._to_dto(dbe)

    async def update_status(
        self,
        session: AsyncSession,
        project_id: UUID,
        run_id: UUID,
        status: str,
        **kwargs,
    ) -> Optional[OvernightRun]:
        """Update overnight run status and related fields."""
        query = select(OvernightRunDBE).where(
            and_(
                OvernightRunDBE.project_id == project_id,
                OvernightRunDBE.id == run_id,
                OvernightRunDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return None

        dbe.status = status
        dbe.updated_at = datetime.utcnow()

        # Handle specific status transitions
        if status == "running" and not dbe.started_at:
            dbe.started_at = datetime.utcnow()
        elif status in ("completed", "failed", "cancelled"):
            dbe.completed_at = datetime.utcnow()

        # Update optional fields
        if "current_workflow_index" in kwargs:
            dbe.current_workflow_index = kwargs["current_workflow_index"]
        if "workflow_results" in kwargs:
            dbe.workflow_results = kwargs["workflow_results"]
        if "total_tokens_input" in kwargs:
            dbe.total_tokens_input = kwargs["total_tokens_input"]
        if "total_tokens_output" in kwargs:
            dbe.total_tokens_output = kwargs["total_tokens_output"]
        if "total_cost" in kwargs:
            dbe.total_cost = kwargs["total_cost"]

        await session.flush()
        return self._to_dto(dbe)

    async def delete(
        self,
        session: AsyncSession,
        project_id: UUID,
        run_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an overnight run."""
        query = select(OvernightRunDBE).where(
            and_(
                OvernightRunDBE.project_id == project_id,
                OvernightRunDBE.id == run_id,
                OvernightRunDBE.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        dbe = result.scalar_one_or_none()
        if not dbe:
            return False

        dbe.deleted_at = datetime.utcnow()
        dbe.deleted_by_id = deleted_by_id
        await session.flush()
        return True

    def _to_dto(self, dbe: OvernightRunDBE) -> OvernightRun:
        workflow_ids = [UUID(wid) for wid in (dbe.workflow_ids or [])]
        workflow_results = [
            WorkflowResult(**r) for r in (dbe.workflow_results or [])
        ]

        return OvernightRun(
            id=dbe.id,
            project_id=dbe.project_id,
            name=dbe.name,
            description=dbe.description,
            workflow_ids=workflow_ids,
            status=dbe.status,
            current_workflow_index=dbe.current_workflow_index or 0,
            workflow_results=workflow_results,
            total_tokens_input=dbe.total_tokens_input or 0,
            total_tokens_output=dbe.total_tokens_output or 0,
            total_cost=float(dbe.total_cost or 0),
            scheduled_for=dbe.scheduled_for,
            started_at=dbe.started_at,
            completed_at=dbe.completed_at,
            config=dbe.config,
            tags=dbe.tags,
            meta=dbe.meta,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )
