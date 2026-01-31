"""Agent trace emission API for LangGraph and agent-based automations.

This module provides APIs for emitting trace spans during agent execution,
enabling observability and debugging of agent workflows.

Usage:
    from bv.runtime.traces import emit_span, TraceSpan, start_span, end_span
    
    # Simple span emission
    emit_span(TraceSpan(
        name="tool_call",
        span_id="unique-id",
        input_payload={"query": "..."},
        output_payload={"result": "..."},
    ))
    
    # Context manager for automatic timing
    with start_span("my_operation", input_payload={"key": "value"}) as span:
        result = do_work()
        span.output_payload = {"result": result}
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

from ._guard import require_bv_run
from .client import OrchestratorClient
from . import context as runtime_context


@dataclass
class TraceSpan:
    """Represents a single trace span in an agent execution.
    
    Attributes:
        name: Human-readable name of the span (e.g., "tool_call", "llm_request").
        span_id: Unique identifier for this span. Auto-generated if not provided.
        parent_span_id: ID of the parent span for hierarchical traces.
        input_payload: Input data for this operation (JSON-serializable).
        output_payload: Output/result of this operation (JSON-serializable).
        start_time: When the span started. Auto-set if not provided.
        end_time: When the span ended.
        duration_ms: Duration in milliseconds (computed from start/end if not set).
        tags: Additional metadata tags for filtering/categorization.
        metadata: Arbitrary metadata for the span.
    """
    name: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)

    def complete(self, output_payload: Optional[Dict[str, Any]] = None) -> None:
        """Mark the span as complete with optional output."""
        self.end_time = datetime.now(timezone.utc)
        if output_payload is not None:
            self.output_payload = output_payload
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_ms = int(delta.total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for API submission."""
        result: Dict[str, Any] = {
            "name": self.name,
            "span_id": self.span_id,
        }
        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id
        if self.input_payload:
            result["input_payload"] = self.input_payload
        if self.output_payload:
            result["output_payload"] = self.output_payload
        if self.start_time:
            result["start_time"] = self.start_time.isoformat().replace("+00:00", "Z")
        if self.end_time:
            result["end_time"] = self.end_time.isoformat().replace("+00:00", "Z")
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.tags:
            result["tags"] = self.tags
        if self.metadata:
            result["span_metadata"] = self.metadata
        return result


# Thread-local span stack for hierarchical tracing
_span_stack: List[TraceSpan] = []


def _get_execution_id() -> Optional[str]:
    """Get the current job execution ID from runtime context."""
    if not runtime_context.is_runtime_initialized():
        return None
    return runtime_context.get_execution_id() or None


def emit_span(span: TraceSpan) -> bool:
    """Emit a trace span to the orchestrator.
    
    Args:
        span: The trace span to emit.
        
    Returns:
        True if the span was successfully emitted, False otherwise.
        
    Note:
        This is a best-effort operation. If the orchestrator is unreachable
        or there's no execution context, the span is silently dropped.
    """
    require_bv_run()
    
    execution_id = _get_execution_id()
    if not execution_id:
        # No execution context, skip silently
        return False
    
    # Path is relative to api_base_url (no /api prefix needed)
    try:
        client = OrchestratorClient()
        client.request(
            "POST",
            f"/agent-traces/{execution_id}/spans",
            json={"spans": [span.to_dict()]}
        )
        return True
    except Exception:
        # Best-effort: don't fail automation on trace emission errors
        return False


def emit_spans(spans: List[TraceSpan]) -> bool:
    """Emit multiple trace spans to the orchestrator in a batch.
    
    Args:
        spans: List of trace spans to emit.
        
    Returns:
        True if the spans were successfully emitted, False otherwise.
    """
    require_bv_run()
    
    execution_id = _get_execution_id()
    if not execution_id or not spans:
        return False
    
    # Path is relative to api_base_url (no /api prefix needed)
    try:
        client = OrchestratorClient()
        client.request(
            "POST",
            f"/agent-traces/{execution_id}/spans",
            json={"spans": [s.to_dict() for s in spans]}
        )
        return True
    except Exception:
        return False


@contextmanager
def start_span(
    name: str,
    parent_span_id: Optional[str] = None,
    input_payload: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Generator[TraceSpan, None, None]:
    """Context manager for creating and emitting a trace span.
    
    Automatically sets start_time on entry, end_time on exit, and emits
    the span when the context exits. Supports hierarchical tracing by
    auto-detecting parent spans.
    
    Usage:
        with start_span("my_operation", input_payload={"key": "value"}) as span:
            result = do_work()
            span.output_payload = {"result": result}
    
    Args:
        name: Name of the span.
        parent_span_id: Explicit parent span ID. If None, uses the current
            active span from the span stack.
        input_payload: Input data for the operation.
        tags: Metadata tags for categorization.
        metadata: Additional metadata.
        
    Yields:
        The TraceSpan object, which can be modified before emission.
    """
    # Auto-detect parent from span stack if not provided
    if parent_span_id is None and _span_stack:
        parent_span_id = _span_stack[-1].span_id
    
    span = TraceSpan(
        name=name,
        parent_span_id=parent_span_id,
        input_payload=input_payload,
        tags=tags,
        metadata=metadata,
    )
    
    _span_stack.append(span)
    try:
        yield span
    finally:
        _span_stack.pop()
        span.complete()
        emit_span(span)


def get_current_span() -> Optional[TraceSpan]:
    """Get the currently active span from the span stack.
    
    Returns:
        The current span, or None if no span is active.
    """
    return _span_stack[-1] if _span_stack else None


def get_current_span_id() -> Optional[str]:
    """Get the span ID of the currently active span.
    
    Useful for passing to child operations that need to link to the parent.
    
    Returns:
        The current span ID, or None if no span is active.
    """
    span = get_current_span()
    return span.span_id if span else None
