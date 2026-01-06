"""
Agent Matrix - Gates Data Access Object

CRUD operations for workflow approval gates.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from oss.src.utils.logging import get_module_logger
from oss.src.dbs.postgres.shared.engine import engine

from extensions.gates.dbes import GateDBE
from extensions.gates.types import (
    Gate,
    GateCreate,
    GateQuery,
    GateStatus,
)

log = get_module_logger(__name__)


class GatesDAO:
    """Data access object for gates."""

    async def create_gate(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: GateCreate,
    ) -> Gate:
        """Create a new gate."""
        async with engine.core_session() as session:
            dbe = GateDBE(
                project_id=project_id,
                created_by_id=user_id,
                workflow_id=dto.workflow_id,
                execution_id=dto.execution_id,
                step_id=dto.step_id,
                gate_type=dto.gate_type.value,
                status="pending",
                config=dto.config,
                context=dto.context,
            )
            session.add(dbe)
            await session.flush()
            return self._gate_to_dto(dbe)

    async def get_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
    ) -> Optional[Gate]:
        """Get a gate by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(GateDBE)
                .where(GateDBE.project_id == project_id)
                .where(GateDBE.id == gate_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._gate_to_dto(dbe) if dbe else None

    async def list_gates(
        self,
        *,
        project_id: UUID,
        query: GateQuery,
    ) -> List[Gate]:
        """List gates with optional filtering."""
        async with engine.core_session() as session:
            stmt = select(GateDBE).where(GateDBE.project_id == project_id)

            if query.workflow_id:
                stmt = stmt.where(GateDBE.workflow_id == query.workflow_id)
            if query.execution_id:
                stmt = stmt.where(GateDBE.execution_id == query.execution_id)
            if query.gate_type:
                stmt = stmt.where(GateDBE.gate_type == query.gate_type.value)
            if query.status:
                stmt = stmt.where(GateDBE.status == query.status.value)

            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            stmt = stmt.order_by(GateDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._gate_to_dto(dbe) for dbe in result.scalars().all()]

    async def approve_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        user_id: UUID,
    ) -> Optional[Gate]:
        """Approve a gate."""
        async with engine.core_session() as session:
            stmt = (
                select(GateDBE)
                .where(GateDBE.project_id == project_id)
                .where(GateDBE.id == gate_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            dbe.status = "approved"
            dbe.reviewed_by = user_id
            dbe.updated_by_id = user_id
            await session.flush()
            return self._gate_to_dto(dbe)

    async def reject_gate(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> Optional[Gate]:
        """Reject a gate."""
        async with engine.core_session() as session:
            stmt = (
                select(GateDBE)
                .where(GateDBE.project_id == project_id)
                .where(GateDBE.id == gate_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            dbe.status = "rejected"
            dbe.reviewed_by = user_id
            dbe.rejection_reason = reason
            dbe.updated_by_id = user_id
            await session.flush()
            return self._gate_to_dto(dbe)

    async def get_pending_for_execution(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
    ) -> List[Gate]:
        """Get all pending gates for an execution."""
        async with engine.core_session() as session:
            stmt = (
                select(GateDBE)
                .where(GateDBE.project_id == project_id)
                .where(GateDBE.execution_id == execution_id)
                .where(GateDBE.status == "pending")
                .order_by(GateDBE.created_at.asc())
            )
            result = await session.execute(stmt)
            return [self._gate_to_dto(dbe) for dbe in result.scalars().all()]

    async def get_gate_for_step(
        self,
        *,
        project_id: UUID,
        execution_id: UUID,
        step_id: str,
    ) -> Optional[Gate]:
        """Get the gate for a specific step in an execution."""
        async with engine.core_session() as session:
            stmt = (
                select(GateDBE)
                .where(GateDBE.project_id == project_id)
                .where(GateDBE.execution_id == execution_id)
                .where(GateDBE.step_id == step_id)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._gate_to_dto(dbe) if dbe else None

    def _gate_to_dto(self, dbe: GateDBE) -> Gate:
        """Convert GateDBE to Gate DTO."""
        return Gate(
            id=dbe.id,
            project_id=dbe.project_id,
            workflow_id=dbe.workflow_id,
            execution_id=dbe.execution_id,
            step_id=dbe.step_id,
            gate_type=dbe.gate_type,
            status=dbe.status,
            reviewed_by=dbe.reviewed_by,
            rejection_reason=dbe.rejection_reason,
            config=dbe.config,
            context=dbe.context,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )
