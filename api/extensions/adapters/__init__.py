# Adapters for Dashboard and CLI integration
from extensions.adapters.routes import (
    EXPRESS_API_ROUTES,
    AGENTA_API_ROUTES,
    get_dashboard_config,
    get_cli_config,
    adapt_agent_response,
)

__all__ = [
    "EXPRESS_API_ROUTES",
    "AGENTA_API_ROUTES",
    "get_dashboard_config",
    "get_cli_config",
    "adapt_agent_response",
]
