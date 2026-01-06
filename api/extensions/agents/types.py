"""
Agent Matrix - Agents Types

Pydantic models for agent DTOs and request/response types.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class AgentScope(str, Enum):
    PERSONAL = "personal"
    TEAM = "team"
    PUBLIC = "public"


class AgentBranch(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


# -----------------------------------------------------------------------------
# Agent DTOs
# -----------------------------------------------------------------------------

class AgentCreate(BaseModel):
    """DTO for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    tools: Optional[List[str]] = None
    scope: Optional[AgentScope] = AgentScope.PERSONAL
    branch: Optional[AgentBranch] = AgentBranch.DEV
    is_public: Optional[bool] = False
    forked_from: Optional[UUID] = None
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class AgentUpdate(BaseModel):
    """DTO for updating an agent."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    tools: Optional[List[str]] = None
    scope: Optional[AgentScope] = None
    branch: Optional[AgentBranch] = None
    is_public: Optional[bool] = None
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class AgentQuery(BaseModel):
    """DTO for querying agents."""
    name: Optional[str] = None
    scope: Optional[AgentScope] = None
    branch: Optional[AgentBranch] = None
    is_public: Optional[bool] = None
    offset: Optional[int] = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=100)


class Agent(BaseModel):
    """Agent DTO."""
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: List[str] = []
    scope: str
    branch: str
    version: int
    is_public: bool
    forked_from: Optional[UUID] = None
    tags: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Agent Version DTOs
# -----------------------------------------------------------------------------

class AgentVersionCreate(BaseModel):
    """DTO for creating an agent version snapshot."""
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[str]] = None
    changelog: Optional[str] = None


class AgentVersion(BaseModel):
    """Agent version DTO."""
    id: UUID
    agent_id: UUID
    version: int
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[str]] = None
    changelog: Optional[str] = None
    created_at: datetime
    created_by_id: UUID

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Agent Rule DTOs
# -----------------------------------------------------------------------------

class AgentRuleCreate(BaseModel):
    """DTO for creating an agent rule."""
    name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., min_length=1, max_length=50)
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 0
    is_active: Optional[bool] = True


class AgentRuleUpdate(BaseModel):
    """DTO for updating an agent rule."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    rule_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class AgentRule(BaseModel):
    """Agent rule DTO."""
    id: UUID
    agent_id: UUID
    name: str
    rule_type: str
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Agent Execution DTOs
# -----------------------------------------------------------------------------

class AgentRunRequest(BaseModel):
    """Request to run an agent."""
    input: str = Field(..., min_length=1)
    workspace_path: Optional[str] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    tools_override: Optional[List[str]] = None
    max_steps: Optional[int] = Field(default=50, ge=1, le=500)


class AgentRunResponse(BaseModel):
    """Response from running an agent."""
    session_id: UUID
    output: str
    tool_calls: List[Dict[str, Any]] = []
    tokens_input: int
    tokens_output: int
    cost: float
    duration_ms: int


class AgentForkRequest(BaseModel):
    """Request to fork an agent."""
    name: Optional[str] = None
    scope: Optional[AgentScope] = AgentScope.PERSONAL


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class AgentCreateRequest(BaseModel):
    """API request for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    scope: Optional[str] = "personal"
    branch: Optional[str] = "dev"
    is_public: Optional[bool] = False
    tags: Optional[Dict[str, Any]] = None

    def to_dto(self) -> AgentCreate:
        return AgentCreate(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=self.tools,
            scope=AgentScope(self.scope) if self.scope else AgentScope.PERSONAL,
            branch=AgentBranch(self.branch) if self.branch else AgentBranch.DEV,
            is_public=self.is_public,
            tags=self.tags,
        )


class AgentUpdateRequest(BaseModel):
    """API request for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    scope: Optional[str] = None
    branch: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[Dict[str, Any]] = None

    def to_dto(self) -> AgentUpdate:
        return AgentUpdate(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=self.tools,
            scope=AgentScope(self.scope) if self.scope else None,
            branch=AgentBranch(self.branch) if self.branch else None,
            is_public=self.is_public,
            tags=self.tags,
        )


class AgentResponse(BaseModel):
    """API response for an agent."""
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: List[str] = []
    scope: str
    branch: str
    version: int
    is_public: bool
    forked_from: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: Agent) -> "AgentResponse":
        return cls(
            id=str(dto.id),
            project_id=str(dto.project_id),
            name=dto.name,
            description=dto.description,
            system_prompt=dto.system_prompt,
            model=dto.model,
            temperature=dto.temperature,
            max_tokens=dto.max_tokens,
            tools=dto.tools,
            scope=dto.scope,
            branch=dto.branch,
            version=dto.version,
            is_public=dto.is_public,
            forked_from=str(dto.forked_from) if dto.forked_from else None,
            tags=dto.tags,
            created_at=dto.created_at.isoformat(),
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )


class AgentsListResponse(BaseModel):
    """API response for listing agents."""
    agents: List[AgentResponse]
    total: int
    offset: int
    limit: int
