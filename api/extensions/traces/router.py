"""
Agent Matrix - Traces Router

REST API endpoints for trace/span operations.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException

from extensions.traces.service import AgentMatrixTracingService
from extensions.traces.types import (
    SpanCreate,
    SpanUpdate,
    Span,
    TraceTree,
    TraceQuery,
    AgentMatrixSpanType,
)


class TracesRouter:
    """Router for trace operations."""

    def __init__(self, service: AgentMatrixTracingService):
        self.service = service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        router = self.router

        @router.post("/spans", response_model=Span)
        async def create_span(
            payload: SpanCreate,
            request: Request,
        ):
            """Create a new span."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            return await self.service.create_span(project_id, payload)

        @router.patch("/spans/{span_id}", response_model=Span)
        async def update_span(
            span_id: UUID,
            payload: SpanUpdate,
            request: Request,
        ):
            """Update an existing span."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            return await self.service.update_span(project_id, span_id, payload)

        @router.get("/spans/{span_id}", response_model=Span)
        async def get_span(
            span_id: UUID,
            request: Request,
        ):
            """Get a single span by ID."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            span = await self.service.get_span(project_id, span_id)
            if not span:
                raise HTTPException(status_code=404, detail="Span not found")
            return span

        @router.get("/sessions/{session_id}/tree", response_model=TraceTree)
        async def get_trace_tree(
            session_id: UUID,
            request: Request,
        ):
            """
            Get hierarchical trace tree for visualization.

            Returns all spans for a session organized as a nested tree structure.
            """
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            return await self.service.get_trace_tree(project_id, session_id)

        @router.get("/sessions/{session_id}/spans", response_model=list[Span])
        async def list_spans_by_session(
            session_id: UUID,
            request: Request,
        ):
            """Get all spans for a session (flat list)."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            return await self.service.list_spans_by_trace(project_id, session_id)

        @router.get("/spans", response_model=list[Span])
        async def list_spans(
            request: Request,
            session_id: Optional[UUID] = Query(None),
            span_type: Optional[AgentMatrixSpanType] = Query(None),
            status: Optional[str] = Query(None),
            limit: int = Query(100, le=1000),
            offset: int = Query(0),
        ):
            """Query spans with filters."""
            project_id = getattr(request.state, "project_id", None)
            if not project_id:
                raise HTTPException(status_code=400, detail="Project ID required")

            query = TraceQuery(
                project_id=project_id,
                session_id=session_id,
                span_type=span_type,
                status=status,
                limit=limit,
                offset=offset,
            )
            return await self.service.list_spans(query)
