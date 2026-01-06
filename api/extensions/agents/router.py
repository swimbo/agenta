"""
Agent Matrix - Agents Router

FastAPI router for agent endpoints.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status, Query

from oss.src.utils.logging import get_module_logger

from extensions.agents.service import AgentsService
from extensions.agents.types import (
    AgentCreate,
    AgentUpdate,
    AgentQuery,
    AgentVersionCreate,
    AgentRuleCreate,
    AgentRuleUpdate,
    AgentRunRequest,
    AgentForkRequest,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentsListResponse,
    AgentScope,
    AgentBranch,
)

log = get_module_logger(__name__)


class AgentsRouter:
    """Router for agent endpoints."""

    def __init__(self, agents_service: AgentsService):
        self.agents_service = agents_service
        self.router = APIRouter()

        # Agent CRUD
        self.router.add_api_route(
            "/",
            self.create_agent,
            methods=["POST"],
            operation_id="create_agent",
            status_code=status.HTTP_201_CREATED,
            response_model=AgentResponse,
        )

        self.router.add_api_route(
            "/",
            self.list_agents,
            methods=["GET"],
            operation_id="list_agents",
            status_code=status.HTTP_200_OK,
            response_model=AgentsListResponse,
        )

        self.router.add_api_route(
            "/{agent_id}",
            self.get_agent,
            methods=["GET"],
            operation_id="get_agent",
            status_code=status.HTTP_200_OK,
            response_model=AgentResponse,
        )

        self.router.add_api_route(
            "/{agent_id}",
            self.update_agent,
            methods=["PUT"],
            operation_id="update_agent",
            status_code=status.HTTP_200_OK,
            response_model=AgentResponse,
        )

        self.router.add_api_route(
            "/{agent_id}",
            self.delete_agent,
            methods=["DELETE"],
            operation_id="delete_agent",
            status_code=status.HTTP_204_NO_CONTENT,
        )

        # Agent execution
        self.router.add_api_route(
            "/{agent_id}/run",
            self.run_agent,
            methods=["POST"],
            operation_id="run_agent",
            status_code=status.HTTP_200_OK,
        )

        self.router.add_api_route(
            "/{agent_id}/fork",
            self.fork_agent,
            methods=["POST"],
            operation_id="fork_agent",
            status_code=status.HTTP_201_CREATED,
            response_model=AgentResponse,
        )

        # Agent versions
        self.router.add_api_route(
            "/{agent_id}/versions",
            self.list_versions,
            methods=["GET"],
            operation_id="list_agent_versions",
            status_code=status.HTTP_200_OK,
        )

        self.router.add_api_route(
            "/{agent_id}/versions",
            self.create_version,
            methods=["POST"],
            operation_id="create_agent_version",
            status_code=status.HTTP_201_CREATED,
        )

        self.router.add_api_route(
            "/{agent_id}/versions/{version}",
            self.get_version,
            methods=["GET"],
            operation_id="get_agent_version",
            status_code=status.HTTP_200_OK,
        )

        # Agent rules
        self.router.add_api_route(
            "/{agent_id}/rules",
            self.list_rules,
            methods=["GET"],
            operation_id="list_agent_rules",
            status_code=status.HTTP_200_OK,
        )

        self.router.add_api_route(
            "/{agent_id}/rules",
            self.create_rule,
            methods=["POST"],
            operation_id="create_agent_rule",
            status_code=status.HTTP_201_CREATED,
        )

        self.router.add_api_route(
            "/{agent_id}/rules/{rule_id}",
            self.update_rule,
            methods=["PUT"],
            operation_id="update_agent_rule",
            status_code=status.HTTP_200_OK,
        )

        self.router.add_api_route(
            "/{agent_id}/rules/{rule_id}",
            self.delete_rule,
            methods=["DELETE"],
            operation_id="delete_agent_rule",
            status_code=status.HTTP_204_NO_CONTENT,
        )

        self.router.add_api_route(
            "/{agent_id}/rules/{rule_id}/toggle",
            self.toggle_rule,
            methods=["POST"],
            operation_id="toggle_agent_rule",
            status_code=status.HTTP_200_OK,
        )

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _get_project_id(self, request: Request) -> UUID:
        """Get project_id from request state."""
        project_id = getattr(request.state, "project_id", None)
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project ID is required",
            )
        return UUID(str(project_id))

    def _get_user_id(self, request: Request) -> UUID:
        """Get user_id from request state."""
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID is required",
            )
        return UUID(str(user_id))

    # -------------------------------------------------------------------------
    # Agent CRUD endpoints
    # -------------------------------------------------------------------------

    async def create_agent(
        self,
        request: Request,
        payload: AgentCreateRequest,
    ) -> AgentResponse:
        """Create a new agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        agent = await self.agents_service.create_agent(
            project_id=project_id,
            user_id=user_id,
            dto=payload.to_dto(),
        )
        return AgentResponse.from_dto(agent)

    async def list_agents(
        self,
        request: Request,
        name: Optional[str] = Query(None),
        scope: Optional[str] = Query(None),
        branch: Optional[str] = Query(None),
        is_public: Optional[bool] = Query(None),
        offset: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
    ) -> AgentsListResponse:
        """List agents with optional filtering."""
        project_id = self._get_project_id(request)

        query = AgentQuery(
            name=name,
            scope=AgentScope(scope) if scope else None,
            branch=AgentBranch(branch) if branch else None,
            is_public=is_public,
            offset=offset,
            limit=limit,
        )

        agents = await self.agents_service.list_agents(
            project_id=project_id,
            query=query,
        )

        return AgentsListResponse(
            agents=[AgentResponse.from_dto(a) for a in agents],
            total=len(agents),  # TODO: Get actual count from DAO
            offset=offset,
            limit=limit,
        )

    async def get_agent(
        self,
        request: Request,
        agent_id: UUID,
    ) -> AgentResponse:
        """Get an agent by ID."""
        project_id = self._get_project_id(request)

        agent = await self.agents_service.get_agent(
            project_id=project_id,
            agent_id=agent_id,
        )

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return AgentResponse.from_dto(agent)

    async def update_agent(
        self,
        request: Request,
        agent_id: UUID,
        payload: AgentUpdateRequest,
    ) -> AgentResponse:
        """Update an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        agent = await self.agents_service.update_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=payload.to_dto(),
        )

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return AgentResponse.from_dto(agent)

    async def delete_agent(
        self,
        request: Request,
        agent_id: UUID,
    ) -> None:
        """Delete an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        deleted = await self.agents_service.delete_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

    # -------------------------------------------------------------------------
    # Agent execution endpoints
    # -------------------------------------------------------------------------

    async def run_agent(
        self,
        request: Request,
        agent_id: UUID,
        payload: AgentRunRequest,
    ):
        """Run an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        result = await self.agents_service.run_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=payload,
        )

        return result

    async def fork_agent(
        self,
        request: Request,
        agent_id: UUID,
        payload: AgentForkRequest,
    ) -> AgentResponse:
        """Fork an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        agent = await self.agents_service.fork_agent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=payload,
        )

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return AgentResponse.from_dto(agent)

    # -------------------------------------------------------------------------
    # Agent version endpoints
    # -------------------------------------------------------------------------

    async def list_versions(
        self,
        request: Request,
        agent_id: UUID,
    ):
        """List all versions of an agent."""
        project_id = self._get_project_id(request)

        versions = await self.agents_service.list_versions(
            project_id=project_id,
            agent_id=agent_id,
        )

        return {"versions": versions}

    async def create_version(
        self,
        request: Request,
        agent_id: UUID,
        payload: AgentVersionCreate,
    ):
        """Create a new version snapshot of an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        version = await self.agents_service.create_version(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=payload,
        )

        return version

    async def get_version(
        self,
        request: Request,
        agent_id: UUID,
        version: int,
    ):
        """Get a specific version of an agent."""
        project_id = self._get_project_id(request)

        agent_version = await self.agents_service.get_version(
            project_id=project_id,
            agent_id=agent_id,
            version=version,
        )

        if not agent_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found for agent {agent_id}",
            )

        return agent_version

    # -------------------------------------------------------------------------
    # Agent rule endpoints
    # -------------------------------------------------------------------------

    async def list_rules(
        self,
        request: Request,
        agent_id: UUID,
    ):
        """List all rules for an agent."""
        project_id = self._get_project_id(request)

        rules = await self.agents_service.list_rules(
            project_id=project_id,
            agent_id=agent_id,
        )

        return {"rules": rules}

    async def create_rule(
        self,
        request: Request,
        agent_id: UUID,
        payload: AgentRuleCreate,
    ):
        """Create a new rule for an agent."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        rule = await self.agents_service.create_rule(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
            dto=payload,
        )

        return rule

    async def update_rule(
        self,
        request: Request,
        agent_id: UUID,
        rule_id: UUID,
        payload: AgentRuleUpdate,
    ):
        """Update an agent rule."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        rule = await self.agents_service.update_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
            dto=payload,
        )

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule {rule_id} not found",
            )

        return rule

    async def delete_rule(
        self,
        request: Request,
        agent_id: UUID,
        rule_id: UUID,
    ) -> None:
        """Delete an agent rule."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        deleted = await self.agents_service.delete_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule {rule_id} not found",
            )

    async def toggle_rule(
        self,
        request: Request,
        agent_id: UUID,
        rule_id: UUID,
    ):
        """Toggle a rule's active state."""
        project_id = self._get_project_id(request)
        user_id = self._get_user_id(request)

        rule = await self.agents_service.toggle_rule(
            project_id=project_id,
            rule_id=rule_id,
            user_id=user_id,
        )

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule {rule_id} not found",
            )

        return rule
