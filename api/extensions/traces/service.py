"""
Agent Matrix - Tracing Service

Wraps Agenta's TracingService to provide Agent Matrix span types
while storing data in Agenta's OpenTelemetry-compatible format.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
import uuid_utils.compat as uuid

from extensions.traces.types import (
    SpanCreate,
    SpanUpdate,
    Span,
    TraceTree,
    TraceQuery,
    SPAN_TYPE_MAPPING,
    AgentMatrixSpanType,
)


class AgentMatrixTracingService:
    """
    Tracing service that maps Agent Matrix span types to Agenta's spans.

    This service wraps Agenta's TracingService while preserving
    our custom span_type semantics (session, tool_call, llm_call, etc.)
    """

    def __init__(self, agenta_tracing_service=None):
        """
        Initialize with optional Agenta tracing service.

        If no service provided, operates in standalone mode using
        direct database access.
        """
        self.agenta_tracing = agenta_tracing_service
        self._spans_cache: dict[UUID, dict] = {}  # In-memory cache for building trees

    async def create_span(
        self,
        project_id: UUID,
        dto: SpanCreate,
    ) -> Span:
        """
        Create a new span.

        Maps Agent Matrix span type to Agenta span type while preserving
        our original type in metadata.
        """
        span_id = uuid.uuid7()
        now = datetime.utcnow()

        # Map to Agenta span type
        agenta_span_type = SPAN_TYPE_MAPPING.get(
            dto.span_type,
            "workflow"
        )

        # Build attributes with our custom span type preserved
        attributes = {
            "ag.type.span": dto.span_type.value,
            "ag.data.inputs": dto.input or {},
            "ag.data.outputs": dto.output or {},
            **(dto.metadata or {}),
        }

        if dto.model:
            attributes["ag.meta.model"] = dto.model
        if dto.tokens_input:
            attributes["ag.meta.tokens.prompt"] = dto.tokens_input
        if dto.tokens_output:
            attributes["ag.meta.tokens.completion"] = dto.tokens_output
        if dto.cost:
            attributes["ag.meta.cost"] = dto.cost

        # If we have Agenta's tracing service, use it
        if self.agenta_tracing:
            agenta_span = await self.agenta_tracing.create_span(
                trace_id=dto.trace_id,
                span_type=agenta_span_type,
                name=dto.name,
                parent_span_id=dto.parent_span_id,
                attributes=attributes,
            )
            span_id = agenta_span.id

        # Build response
        span = Span(
            id=span_id,
            trace_id=dto.trace_id,
            parent_span_id=dto.parent_span_id,
            span_type=dto.span_type.value,
            name=dto.name,
            input=dto.input,
            output=dto.output,
            metadata=dto.metadata,
            start_time=dto.start_time or now,
            end_time=dto.end_time,
            status=dto.status or "ok",
            tokens_input=dto.tokens_input,
            tokens_output=dto.tokens_output,
            cost=dto.cost,
            model=dto.model,
        )

        # Cache for tree building
        self._spans_cache[span_id] = span.model_dump()

        return span

    async def update_span(
        self,
        project_id: UUID,
        span_id: UUID,
        dto: SpanUpdate,
    ) -> Span:
        """Update an existing span."""
        if self.agenta_tracing:
            attributes = {}
            if dto.output:
                attributes["ag.data.outputs"] = dto.output
            if dto.metadata:
                attributes.update(dto.metadata)
            if dto.tokens_input:
                attributes["ag.meta.tokens.prompt"] = dto.tokens_input
            if dto.tokens_output:
                attributes["ag.meta.tokens.completion"] = dto.tokens_output
            if dto.cost:
                attributes["ag.meta.cost"] = dto.cost

            await self.agenta_tracing.update_span(
                span_id=span_id,
                attributes=attributes,
                end_time=dto.end_time,
                status=dto.status,
            )

        # Update cache
        if span_id in self._spans_cache:
            cached = self._spans_cache[span_id]
            if dto.output:
                cached["output"] = dto.output
            if dto.metadata:
                cached["metadata"] = {**(cached.get("metadata") or {}), **dto.metadata}
            if dto.end_time:
                cached["end_time"] = dto.end_time
            if dto.status:
                cached["status"] = dto.status
            if dto.tokens_input:
                cached["tokens_input"] = dto.tokens_input
            if dto.tokens_output:
                cached["tokens_output"] = dto.tokens_output
            if dto.cost:
                cached["cost"] = dto.cost

            return Span(**cached)

        # If not in cache, return minimal response
        return Span(
            id=span_id,
            trace_id=UUID(int=0),  # Placeholder
            span_type="custom",
            name="",
            start_time=datetime.utcnow(),
        )

    async def get_span(
        self,
        project_id: UUID,
        span_id: UUID,
    ) -> Optional[Span]:
        """Get a single span by ID."""
        if span_id in self._spans_cache:
            return Span(**self._spans_cache[span_id])

        if self.agenta_tracing:
            agenta_span = await self.agenta_tracing.get_span(span_id)
            if agenta_span:
                return self._agenta_span_to_dto(agenta_span)

        return None

    async def get_trace_tree(
        self,
        project_id: UUID,
        trace_id: UUID,
    ) -> TraceTree:
        """
        Get hierarchical trace tree for visualization.

        Returns all spans for a trace organized as a nested tree structure.
        """
        spans = await self.list_spans_by_trace(project_id, trace_id)

        # Build tree
        tree = self._build_tree(spans)

        # Calculate totals
        total_tokens_input = sum(s.tokens_input or 0 for s in spans)
        total_tokens_output = sum(s.tokens_output or 0 for s in spans)
        total_cost = sum(s.cost or 0.0 for s in spans)

        # Calculate duration
        duration_ms = None
        if spans:
            start_times = [s.start_time for s in spans if s.start_time]
            end_times = [s.end_time for s in spans if s.end_time]
            if start_times and end_times:
                min_start = min(start_times)
                max_end = max(end_times)
                duration_ms = int((max_end - min_start).total_seconds() * 1000)

        return TraceTree(
            trace_id=trace_id,
            spans=tree,
            total_spans=len(spans),
            total_tokens_input=total_tokens_input,
            total_tokens_output=total_tokens_output,
            total_cost=total_cost,
            duration_ms=duration_ms,
        )

    async def list_spans_by_trace(
        self,
        project_id: UUID,
        trace_id: UUID,
    ) -> list[Span]:
        """Get all spans for a trace."""
        if self.agenta_tracing:
            agenta_spans = await self.agenta_tracing.get_spans_by_trace(trace_id)
            return [self._agenta_span_to_dto(s) for s in agenta_spans]

        # Return from cache
        return [
            Span(**s) for s in self._spans_cache.values()
            if s.get("trace_id") == trace_id
        ]

    async def list_spans(
        self,
        query: TraceQuery,
    ) -> list[Span]:
        """Query spans with filters."""
        if self.agenta_tracing:
            filters = {
                "project_id": query.project_id,
            }
            if query.session_id:
                filters["trace_id"] = query.session_id
            if query.span_type:
                filters["span_type"] = SPAN_TYPE_MAPPING.get(query.span_type, "workflow")
            if query.status:
                filters["status"] = query.status
            if query.start_time_gte:
                filters["start_time_gte"] = query.start_time_gte
            if query.start_time_lte:
                filters["start_time_lte"] = query.start_time_lte

            agenta_spans = await self.agenta_tracing.list_spans(
                filters=filters,
                limit=query.limit,
                offset=query.offset,
            )
            return [self._agenta_span_to_dto(s) for s in agenta_spans]

        # Filter from cache
        spans = list(self._spans_cache.values())

        if query.session_id:
            spans = [s for s in spans if s.get("trace_id") == query.session_id]
        if query.span_type:
            spans = [s for s in spans if s.get("span_type") == query.span_type.value]
        if query.status:
            spans = [s for s in spans if s.get("status") == query.status]

        return [Span(**s) for s in spans[query.offset:query.offset + query.limit]]

    def _build_tree(self, spans: list[Span]) -> list[Span]:
        """Build nested tree from flat span list."""
        by_id = {s.id: s.model_copy() for s in spans}
        root = []

        for span in spans:
            if span.parent_span_id and span.parent_span_id in by_id:
                parent = by_id[span.parent_span_id]
                parent.children.append(by_id[span.id])
            else:
                root.append(by_id[span.id])

        return root

    def _agenta_span_to_dto(self, agenta_span) -> Span:
        """Convert Agenta span to our Span DTO."""
        attributes = agenta_span.attributes or {}

        # Extract our original span type from attributes
        span_type = attributes.get("ag.type.span", "custom")

        return Span(
            id=agenta_span.id,
            trace_id=agenta_span.trace_id,
            parent_span_id=agenta_span.parent_span_id,
            span_type=span_type,
            name=agenta_span.name,
            input=attributes.get("ag.data.inputs"),
            output=attributes.get("ag.data.outputs"),
            metadata={
                k: v for k, v in attributes.items()
                if not k.startswith("ag.")
            },
            start_time=agenta_span.start_time,
            end_time=agenta_span.end_time,
            status=agenta_span.status or "ok",
            tokens_input=attributes.get("ag.meta.tokens.prompt"),
            tokens_output=attributes.get("ag.meta.tokens.completion"),
            cost=attributes.get("ag.meta.cost"),
            model=attributes.get("ag.meta.model"),
        )
