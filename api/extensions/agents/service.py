"""
Agent Matrix - Agents Service

Business logic for agent management.
"""

from typing import Optional, List
from uuid import UUID

from oss.src.utils.logging import get_module_logger

from extensions.agents.dao import AgentsDAO
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
    AgentRunRequest,
    AgentRunResponse,
    AgentForkRequest,
)

log = get_module_logger(__name__)


class AgentsService:
    """Service for agent operations."""

    def __init__(self, agents_dao: AgentsDAO):
        self.dao = agents_dao

    # -------------------------------------------------------------------------
    # Agent CRUD
    # -------------------------------------------------------------------------

    async def create_agent(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        dto: AgentCreate,
    ) -> Agent:
        """Create a new agent."""
        log.info(f"Creating agent: {dto.name} for project {project_id}")
        return await self.dao.create_agent(
            project_id=project_id,
            user_id=user_id,
            dto=dto,
        )

    async def get_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> Optional[Agent]:
        """Get an agent by ID."""
        return await self.dao.get_agent(
            project_id=project_id,
            agent_id=agent_id,
        )

    async def list_agents(
        self,
        *,
        project_id: UUID,
        query: AgentQuery,
    ) -> List[Agent]:
        """List agents with optional filtering."""
        return await self.dao.list_agents(
            project_id=project_id,
            query=query,
        )

    async def update_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentUpdate,
    ) -> Optional[Agent]:
        """Update an agent."""
        log.info(f"Updating agent: {agent_id}")
        return await self.dao.update_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=dto,
        )

    async def delete_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete an agent."""
        log.info(f"Deleting agent: {agent_id}")
        return await self.dao.delete_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
        )

    async def fork_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentForkRequest,
    ) -> Optional[Agent]:
        """Fork an existing agent."""
        # Get the original agent
        original = await self.dao.get_agent(
            project_id=project_id,
            agent_id=agent_id,
        )
        if not original:
            return None

        # Create a new agent based on the original
        fork_dto = AgentCreate(
            name=dto.name or f"{original.name} (Fork)",
            description=original.description,
            system_prompt=original.system_prompt,
            model=original.model,
            temperature=original.temperature,
            max_tokens=original.max_tokens,
            tools=original.tools,
            scope=dto.scope or original.scope,
            branch="dev",  # Always start forks in dev
            is_public=False,  # Forks start as private
            forked_from=original.id,
            tags=original.tags,
            meta=original.meta,
        )

        log.info(f"Forking agent: {agent_id} -> {fork_dto.name}")
        return await self.dao.create_agent(
            project_id=project_id,
            user_id=user_id,
            dto=fork_dto,
        )

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
        """Create a new version snapshot of an agent."""
        log.info(f"Creating version for agent: {agent_id}")
        return await self.dao.create_version(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=dto,
        )

    async def list_versions(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> List[AgentVersion]:
        """List all versions of an agent."""
        return await self.dao.list_versions(
            project_id=project_id,
            agent_id=agent_id,
        )

    async def get_version(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        version: int,
    ) -> Optional[AgentVersion]:
        """Get a specific version of an agent."""
        return await self.dao.get_version(
            project_id=project_id,
            agent_id=agent_id,
            version=version,
        )

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
        """Create a new rule for an agent."""
        log.info(f"Creating rule for agent: {agent_id}")
        return await self.dao.create_rule(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=dto,
        )

    async def list_rules(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
    ) -> List[AgentRule]:
        """List all rules for an agent."""
        return await self.dao.list_rules(
            project_id=project_id,
            agent_id=agent_id,
        )

    async def update_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
        dto: AgentRuleUpdate,
    ) -> Optional[AgentRule]:
        """Update an agent rule."""
        return await self.dao.update_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
            dto=dto,
        )

    async def delete_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete an agent rule."""
        return await self.dao.delete_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
        )

    async def toggle_rule(
        self,
        *,
        project_id: UUID,
        rule_id: UUID,
        user_id: UUID,
    ) -> Optional[AgentRule]:
        """Toggle a rule's active state."""
        return await self.dao.toggle_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
        )

    # -------------------------------------------------------------------------
    # Agent Execution
    # -------------------------------------------------------------------------

    async def run_agent(
        self,
        *,
        project_id: UUID,
        agent_id: UUID,
        user_id: UUID,
        dto: AgentRunRequest,
    ) -> AgentRunResponse:
        """
        Run an agent with the given input.

        Note: Actual execution is delegated to OpenCode via the Bridge.
        This method creates the session and coordinates the execution.
        """
        # Get the agent configuration
        agent = await self.dao.get_agent(
            project_id=project_id,
            agent_id=agent_id,
        )
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # TODO: Wire to Bridge/OpenCode for actual execution
        # For now, return a placeholder response
        # This will be implemented in Phase 6 (Bridge Integration)

        log.info(f"Running agent: {agent_id} with input: {dto.input[:50]}...")

        # Placeholder - actual implementation will use Bridge
        import uuid
        return AgentRunResponse(
            session_id=uuid.uuid4(),
            output="[Execution pending Bridge integration]",
            tool_calls=[],
            tokens_input=0,
            tokens_output=0,
            cost=0.0,
            duration_ms=0,
        )
