"""
Agent Matrix Extensions - Router Mount

This module mounts all Agent Matrix extension routers to the Agenta FastAPI app.
Import and call `mount_extensions(app)` from the main Agenta entrypoint.
"""

from fastapi import FastAPI

# Import DAOs
from extensions.agents.dao import AgentsDAO
from extensions.workflows.dao import WorkflowsDAO
from extensions.sessions.dao import SessionsDAO
from extensions.interventions.dao import InterventionsDAO
from extensions.gates.dao import GatesDAO
from extensions.meta_sessions.dao import MetaSessionsDAO
from extensions.artifacts.dao import ArtifactsDAO
from extensions.overnights.dao import OvernightsDAO

# Import Services
from extensions.agents.service import AgentsService
from extensions.workflows.service import WorkflowsService
from extensions.sessions.service import SessionsService
from extensions.interventions.service import InterventionsService
from extensions.gates.service import GatesService
from extensions.meta_sessions.service import MetaSessionsService
from extensions.artifacts.service import ArtifactsService
from extensions.overnights.service import OvernightsService
from extensions.traces.service import AgentMatrixTracingService

# Import Routers
from extensions.agents.router import AgentsRouter
from extensions.workflows.router import WorkflowsRouter
from extensions.sessions.router import SessionsRouter
from extensions.interventions.router import InterventionsRouter
from extensions.gates.router import GatesRouter
from extensions.meta_sessions.router import MetaSessionsRouter
from extensions.artifacts.router import ArtifactsRouter
from extensions.overnights.router import OvernightsRouter
from extensions.traces.router import TracesRouter


def mount_extensions(app: FastAPI, agenta_tracing_service=None):
    """
    Mount all Agent Matrix extension routers to the FastAPI app.

    Args:
        app: FastAPI application instance
        agenta_tracing_service: Optional Agenta TracingService for trace integration
    """
    # Initialize DAOs
    agents_dao = AgentsDAO()
    workflows_dao = WorkflowsDAO()
    sessions_dao = SessionsDAO()
    interventions_dao = InterventionsDAO()
    gates_dao = GatesDAO()
    meta_sessions_dao = MetaSessionsDAO()
    artifacts_dao = ArtifactsDAO()
    overnights_dao = OvernightsDAO()

    # Initialize Services
    agents_service = AgentsService(agents_dao)
    workflows_service = WorkflowsService(workflows_dao)
    sessions_service = SessionsService(sessions_dao)
    interventions_service = InterventionsService(interventions_dao, workflows_service)
    gates_service = GatesService(gates_dao)
    meta_sessions_service = MetaSessionsService(meta_sessions_dao, agents_service)
    artifacts_service = ArtifactsService(artifacts_dao)
    overnights_service = OvernightsService(overnights_dao, workflows_service)
    traces_service = AgentMatrixTracingService(agenta_tracing_service)

    # Initialize Routers
    agents_router = AgentsRouter(agents_service)
    workflows_router = WorkflowsRouter(workflows_service)
    sessions_router = SessionsRouter(sessions_service)
    interventions_router = InterventionsRouter(interventions_service)
    gates_router = GatesRouter(gates_service)
    meta_sessions_router = MetaSessionsRouter(meta_sessions_service)
    artifacts_router = ArtifactsRouter(artifacts_service)
    overnights_router = OvernightsRouter(overnights_service)
    traces_router = TracesRouter(traces_service)

    # Mount routers with /api prefix
    app.include_router(agents_router.router, prefix="/api/agents", tags=["Agents"])
    app.include_router(workflows_router.router, prefix="/api/workflows", tags=["Workflows"])
    app.include_router(sessions_router.router, prefix="/api/sessions", tags=["Sessions"])
    app.include_router(interventions_router.router, prefix="/api/interventions", tags=["Interventions"])
    app.include_router(gates_router.router, prefix="/api/gates", tags=["Gates"])
    app.include_router(meta_sessions_router.router, prefix="/api/meta-sessions", tags=["Meta Sessions"])
    app.include_router(artifacts_router.router, prefix="/api/artifacts", tags=["Artifacts"])
    app.include_router(overnights_router.router, prefix="/api/overnights", tags=["Overnight Runs"])
    app.include_router(traces_router.router, prefix="/api/traces", tags=["Traces"])

    return {
        "agents": agents_service,
        "workflows": workflows_service,
        "sessions": sessions_service,
        "interventions": interventions_service,
        "gates": gates_service,
        "meta_sessions": meta_sessions_service,
        "artifacts": artifacts_service,
        "overnights": overnights_service,
        "traces": traces_service,
    }
