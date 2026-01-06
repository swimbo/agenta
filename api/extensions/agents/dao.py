"""
Agent Matrix - Agents Data Access Object

CRUD operations for agents, versions, rules, and skills.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from oss.src.utils.logging import get_module_logger
from oss.src.dbs.postgres.shared.engine import engine

from extensions.agents.dbes import (
    AgentDBE,
    AgentVersionDBE,
    AgentRuleDBE,
    AgentSkillDBE,
    RuleExecutionDBE,
)
from extensions.agents.types import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentQuery,
    AgentVersion,
    AgentVersionCreate,
    AgentRule,
    AgentRuleCreate,
    AgentRuleUpdate,
)

log = get_module_logger(__name__)


class AgentsDAO:
    """Data access object for agents and related entities."""

    # -------------------------------------------------------------------------
    # Agents CRUD
    # -------------------------------------------------------------------------

    async def create_agent(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: AgentCreate,
    ) -> Agent:
        """Create a new agent."""
        async with engine.core_session() as session:
            dbe = AgentDBE(
                project_id=project_id,
                created_by_id=user_id,
                name=dto.name,
                description=dto.description,
                system_prompt=dto.system_prompt,
                model=dto.model,
                temperature=dto.temperature,
                max_tokens=dto.max_tokens,
                tools=dto.tools or [],
                scope=dto.scope or "personal",
                branch=dto.branch or "dev",
                is_public=dto.is_public or False,
                forked_from=dto.forked_from,
                tags=dto.tags,
                meta=dto.meta,
            )
            session.add(dbe)
            await session.flush()
            return self._agent_to_dto(dbe)

    async def get_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> Optional[Agent]:
        """Get an agent by ID."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentDBE)
                .where(AgentDBE.project_id == project_id)
                .where(AgentDBE.id == agent_id)
                .where(AgentDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._agent_to_dto(dbe) if dbe else None

    async def list_agents(
        self,
        *,
        project_id: UUID,
        query: AgentQuery,
    ) -> List[Agent]:
        """List agents with optional filtering."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentDBE)
                .where(AgentDBE.project_id == project_id)
                .where(AgentDBE.deleted_at.is_(None))
            )

            if query.scope:
                stmt = stmt.where(AgentDBE.scope == query.scope)
            if query.branch:
                stmt = stmt.where(AgentDBE.branch == query.branch)
            if query.is_public is not None:
                stmt = stmt.where(AgentDBE.is_public == query.is_public)
            if query.name:
                stmt = stmt.where(AgentDBE.name.ilike(f"%{query.name}%"))

            # Pagination
            if query.offset:
                stmt = stmt.offset(query.offset)
            if query.limit:
                stmt = stmt.limit(query.limit)

            # Ordering
            stmt = stmt.order_by(AgentDBE.created_at.desc())

            result = await session.execute(stmt)
            return [self._agent_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentUpdate,
    ) -> Optional[Agent]:
        """Update an agent."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentDBE)
                .where(AgentDBE.project_id == project_id)
                .where(AgentDBE.id == agent_id)
                .where(AgentDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            # Update fields if provided
            if dto.name is not None:
                dbe.name = dto.name
            if dto.description is not None:
                dbe.description = dto.description
            if dto.system_prompt is not None:
                dbe.system_prompt = dto.system_prompt
            if dto.model is not None:
                dbe.model = dto.model
            if dto.temperature is not None:
                dbe.temperature = dto.temperature
            if dto.max_tokens is not None:
                dbe.max_tokens = dto.max_tokens
            if dto.tools is not None:
                dbe.tools = dto.tools
            if dto.scope is not None:
                dbe.scope = dto.scope
            if dto.branch is not None:
                dbe.branch = dto.branch
            if dto.is_public is not None:
                dbe.is_public = dto.is_public
            if dto.tags is not None:
                dbe.tags = dto.tags
            if dto.meta is not None:
                dbe.meta = dto.meta

            dbe.updated_by_id = user_id
            await session.flush()
            return self._agent_to_dto(dbe)

    async def delete_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete an agent."""
        async with engine.core_session() as session:
            stmt = (
                update(AgentDBE)
                .where(AgentDBE.project_id == project_id)
                .where(AgentDBE.id == agent_id)
                .where(AgentDBE.deleted_at.is_(None))
                .values(
                    deleted_at=func.now(),
                    deleted_by_id=user_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    # -------------------------------------------------------------------------
    # Agent Versions
    # -------------------------------------------------------------------------

    async def create_version(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentVersionCreate,
    ) -> AgentVersion:
        """Create a new agent version snapshot."""
        async with engine.core_session() as session:
            # Get current max version
            stmt = (
                select(func.max(AgentVersionDBE.version))
                .where(AgentVersionDBE.project_id == project_id)
                .where(AgentVersionDBE.agent_id == agent_id)
            )
            result = await session.execute(stmt)
            max_version = result.scalar() or 0

            dbe = AgentVersionDBE(
                project_id=project_id,
                agent_id=agent_id,
                created_by_id=user_id,
                version=max_version + 1,
                system_prompt=dto.system_prompt,
                model=dto.model,
                temperature=dto.temperature,
                tools=dto.tools,
                changelog=dto.changelog,
            )
            session.add(dbe)
            await session.flush()

            # Update agent's version number
            await session.execute(
                update(AgentDBE)
                .where(AgentDBE.project_id == project_id)
                .where(AgentDBE.id == agent_id)
                .values(version=max_version + 1)
            )

            return self._version_to_dto(dbe)

    async def list_versions(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> List[AgentVersion]:
        """List all versions of an agent."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentVersionDBE)
                .where(AgentVersionDBE.project_id == project_id)
                .where(AgentVersionDBE.agent_id == agent_id)
                .order_by(AgentVersionDBE.version.desc())
            )
            result = await session.execute(stmt)
            return [self._version_to_dto(dbe) for dbe in result.scalars().all()]

    async def get_version(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        version: int,
    ) -> Optional[AgentVersion]:
        """Get a specific version of an agent."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentVersionDBE)
                .where(AgentVersionDBE.project_id == project_id)
                .where(AgentVersionDBE.agent_id == agent_id)
                .where(AgentVersionDBE.version == version)
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()
            return self._version_to_dto(dbe) if dbe else None

    # -------------------------------------------------------------------------
    # Agent Rules
    # -------------------------------------------------------------------------

    async def create_rule(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentRuleCreate,
    ) -> AgentRule:
        """Create a new agent rule."""
        async with engine.core_session() as session:
            dbe = AgentRuleDBE(
                project_id=project_id,
                agent_id=agent_id,
                created_by_id=user_id,
                name=dto.name,
                rule_type=dto.rule_type,
                condition=dto.condition,
                action=dto.action,
                priority=dto.priority or 0,
                is_active=dto.is_active if dto.is_active is not None else True,
            )
            session.add(dbe)
            await session.flush()
            return self._rule_to_dto(dbe)

    async def list_rules(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> List[AgentRule]:
        """List all rules for an agent."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentRuleDBE)
                .where(AgentRuleDBE.project_id == project_id)
                .where(AgentRuleDBE.agent_id == agent_id)
                .where(AgentRuleDBE.deleted_at.is_(None))
                .order_by(AgentRuleDBE.priority.desc())
            )
            result = await session.execute(stmt)
            return [self._rule_to_dto(dbe) for dbe in result.scalars().all()]

    async def update_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
        dto: AgentRuleUpdate,
    ) -> Optional[AgentRule]:
        """Update an agent rule."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentRuleDBE)
                .where(AgentRuleDBE.project_id == project_id)
                .where(AgentRuleDBE.id == rule_id)
                .where(AgentRuleDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            if dto.name is not None:
                dbe.name = dto.name
            if dto.rule_type is not None:
                dbe.rule_type = dto.rule_type
            if dto.condition is not None:
                dbe.condition = dto.condition
            if dto.action is not None:
                dbe.action = dto.action
            if dto.priority is not None:
                dbe.priority = dto.priority
            if dto.is_active is not None:
                dbe.is_active = dto.is_active

            dbe.updated_by_id = user_id
            await session.flush()
            return self._rule_to_dto(dbe)

    async def delete_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete an agent rule."""
        async with engine.core_session() as session:
            stmt = (
                update(AgentRuleDBE)
                .where(AgentRuleDBE.project_id == project_id)
                .where(AgentRuleDBE.id == rule_id)
                .where(AgentRuleDBE.deleted_at.is_(None))
                .values(
                    deleted_at=func.now(),
                    deleted_by_id=user_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def toggle_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
    ) -> Optional[AgentRule]:
        """Toggle a rule's active state."""
        async with engine.core_session() as session:
            stmt = (
                select(AgentRuleDBE)
                .where(AgentRuleDBE.project_id == project_id)
                .where(AgentRuleDBE.id == rule_id)
                .where(AgentRuleDBE.deleted_at.is_(None))
            )
            result = await session.execute(stmt)
            dbe = result.scalars().first()

            if not dbe:
                return None

            dbe.is_active = not dbe.is_active
            dbe.updated_by_id = user_id
            await session.flush()
            return self._rule_to_dto(dbe)

    # -------------------------------------------------------------------------
    # DTO Mappings
    # -------------------------------------------------------------------------

    def _agent_to_dto(self, dbe: AgentDBE) -> Agent:
        """Convert AgentDBE to Agent DTO."""
        return Agent(
            id=dbe.id,
            project_id=dbe.project_id,
            name=dbe.name,
            description=dbe.description,
            system_prompt=dbe.system_prompt,
            model=dbe.model,
            temperature=dbe.temperature,
            max_tokens=dbe.max_tokens,
            tools=dbe.tools or [],
            scope=dbe.scope,
            branch=dbe.branch,
            version=dbe.version,
            is_public=dbe.is_public,
            forked_from=dbe.forked_from,
            tags=dbe.tags,
            meta=dbe.meta,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
            created_by_id=dbe.created_by_id,
        )

    def _version_to_dto(self, dbe: AgentVersionDBE) -> AgentVersion:
        """Convert AgentVersionDBE to AgentVersion DTO."""
        return AgentVersion(
            id=dbe.id,
            agent_id=dbe.agent_id,
            version=dbe.version,
            system_prompt=dbe.system_prompt,
            model=dbe.model,
            temperature=dbe.temperature,
            tools=dbe.tools,
            changelog=dbe.changelog,
            created_at=dbe.created_at,
            created_by_id=dbe.created_by_id,
        )

    def _rule_to_dto(self, dbe: AgentRuleDBE) -> AgentRule:
        """Convert AgentRuleDBE to AgentRule DTO."""
        return AgentRule(
            id=dbe.id,
            agent_id=dbe.agent_id,
            name=dbe.name,
            rule_type=dbe.rule_type,
            condition=dbe.condition,
            action=dbe.action,
            priority=dbe.priority,
            is_active=dbe.is_active,
            created_at=dbe.created_at,
            updated_at=dbe.updated_at,
        )
