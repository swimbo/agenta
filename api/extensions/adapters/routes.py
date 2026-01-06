"""
Agent Matrix - API Route Configuration

Defines the route mappings for Dashboard and CLI clients.
This module provides the API routes for both the old Express API
and the new Agenta FastAPI endpoints.
"""

# =============================================================================
# Route Mappings
# =============================================================================

# Old Express API routes (for backward compatibility)
EXPRESS_API_ROUTES = {
    # Auth
    "login": "/api/v1/auth/login",
    "logout": "/api/v1/auth/logout",
    "me": "/api/v1/auth/me",

    # Agents
    "agents": "/api/v1/agents",
    "agent": "/api/v1/agents/{id}",
    "agent_run": "/api/v1/agents/{id}/run",
    "agent_versions": "/api/v1/agents/{id}/versions",
    "agent_rules": "/api/v1/agents/{id}/rules",

    # Workflows
    "workflows": "/api/v1/workflows",
    "workflow": "/api/v1/workflows/{id}",
    "workflow_execute": "/api/v1/workflows/{id}/execute",
    "workflow_executions": "/api/v1/workflows/{id}/executions",

    # Sessions
    "sessions": "/api/v1/sessions",
    "session": "/api/v1/sessions/{id}",
    "session_messages": "/api/v1/sessions/{id}/messages",

    # Interventions & Gates
    "interventions": "/api/v1/interventions",
    "gates": "/api/v1/gates",

    # Meta Sessions
    "meta_sessions": "/api/v1/meta-sessions",
    "meta_session": "/api/v1/meta-sessions/{id}",

    # Artifacts
    "artifacts": "/api/v1/artifacts",
    "artifact": "/api/v1/artifacts/{id}",

    # Overnight Runs
    "overnights": "/api/v1/overnights",
    "overnight": "/api/v1/overnights/{id}",

    # Traces
    "traces": "/api/v1/traces",
    "trace_tree": "/api/v1/sessions/{id}/tree",

    # Teams
    "teams": "/api/v1/teams",
    "team": "/api/v1/teams/{id}",

    # Settings
    "settings": "/api/v1/settings",
    "api_keys": "/api/v1/settings/api-keys",
    "models": "/api/v1/settings/models",
}

# New Agenta FastAPI routes
AGENTA_API_ROUTES = {
    # Auth - Agenta uses Supertokens
    "login": "/api/auth/login",
    "logout": "/api/auth/logout",
    "me": "/api/auth/me",

    # Agent Matrix Extensions
    "agents": "/api/agents",
    "agent": "/api/agents/{id}",
    "agent_run": "/api/agents/{id}/run",
    "agent_versions": "/api/agents/{id}/versions",
    "agent_rules": "/api/agents/{id}/rules",

    "workflows": "/api/workflows",
    "workflow": "/api/workflows/{id}",
    "workflow_execute": "/api/workflows/{id}/execute",
    "workflow_executions": "/api/workflows/{id}/executions",

    "sessions": "/api/sessions",
    "session": "/api/sessions/{id}",
    "session_messages": "/api/sessions/{id}/messages",

    "interventions": "/api/interventions",
    "gates": "/api/gates",

    "meta_sessions": "/api/meta-sessions",
    "meta_session": "/api/meta-sessions/{id}",

    "artifacts": "/api/artifacts",
    "artifact": "/api/artifacts/{id}",

    "overnights": "/api/overnights",
    "overnight": "/api/overnights/{id}",

    "traces": "/api/traces",
    "trace_tree": "/api/traces/sessions/{id}/tree",

    # Agenta built-in routes
    "evaluations": "/api/preview/evaluations",
    "testsets": "/api/preview/testsets",
    "tracing": "/api/tracing",
    "organizations": "/api/organizations",
    "workspaces": "/api/workspaces",
    "projects": "/api/projects",

    # Settings via Agenta's Vault
    "vault": "/api/vault",
    "api_keys": "/api/vault/v1/secrets",
}

# =============================================================================
# Client Configuration
# =============================================================================

def get_dashboard_config(use_agenta: bool = True) -> dict:
    """
    Get configuration for the Dashboard client.

    Args:
        use_agenta: Whether to use Agenta API (True) or Express API (False)

    Returns:
        Configuration dict with API base URL and routes
    """
    if use_agenta:
        return {
            "api_base_url": "http://localhost/api",
            "routes": AGENTA_API_ROUTES,
            "auth_provider": "supertokens",
        }
    else:
        return {
            "api_base_url": "http://localhost:4000/api/v1",
            "routes": EXPRESS_API_ROUTES,
            "auth_provider": "jwt",
        }


def get_cli_config(use_agenta: bool = True) -> dict:
    """
    Get configuration for the CLI client.

    Args:
        use_agenta: Whether to use Agenta API (True) or Express API (False)

    Returns:
        Configuration dict with API base URL and routes
    """
    if use_agenta:
        return {
            "api_base_url": "http://localhost/api",
            "routes": AGENTA_API_ROUTES,
            "auth_method": "api_key",  # CLI uses API key auth
        }
    else:
        return {
            "api_base_url": "http://localhost:4000/api/v1",
            "routes": EXPRESS_API_ROUTES,
            "auth_method": "jwt",
        }


# =============================================================================
# Response Adapters
# =============================================================================

def adapt_agent_response(agenta_response: dict, to_express: bool = False) -> dict:
    """
    Adapt agent response between Agenta and Express formats.

    The main differences are:
    - Agenta uses project_id, Express uses team_id
    - Agenta uses created_by_id, Express uses createdBy
    - Agenta returns ISO timestamps, Express may use epoch
    """
    if to_express:
        return {
            "id": agenta_response.get("id"),
            "name": agenta_response.get("name"),
            "description": agenta_response.get("description"),
            "systemPrompt": agenta_response.get("system_prompt"),
            "model": agenta_response.get("model"),
            "temperature": agenta_response.get("temperature"),
            "tools": agenta_response.get("tools", []),
            "scope": agenta_response.get("scope"),
            "branch": agenta_response.get("branch"),
            "version": agenta_response.get("version"),
            "isPublic": agenta_response.get("is_public"),
            "forkedFrom": agenta_response.get("forked_from"),
            "teamId": agenta_response.get("project_id"),
            "createdBy": agenta_response.get("created_by_id"),
            "createdAt": agenta_response.get("created_at"),
            "updatedAt": agenta_response.get("updated_at"),
        }
    else:
        # Express to Agenta format
        return {
            "id": agenta_response.get("id"),
            "project_id": agenta_response.get("teamId"),
            "name": agenta_response.get("name"),
            "description": agenta_response.get("description"),
            "system_prompt": agenta_response.get("systemPrompt"),
            "model": agenta_response.get("model"),
            "temperature": agenta_response.get("temperature"),
            "tools": agenta_response.get("tools", []),
            "scope": agenta_response.get("scope"),
            "branch": agenta_response.get("branch"),
            "version": agenta_response.get("version"),
            "is_public": agenta_response.get("isPublic"),
            "forked_from": agenta_response.get("forkedFrom"),
            "created_by_id": agenta_response.get("createdBy"),
            "created_at": agenta_response.get("createdAt"),
            "updated_at": agenta_response.get("updatedAt"),
        }
