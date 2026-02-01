"""Phoenix tracer integration for Probe layer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class TraceSpan:
    """A single span in a trace."""
    span_id: str
    name: str
    start_time: str
    end_time: Optional[str] = None
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    status: str = "OK"


@dataclass
class TraceContext:
    """Context for a single exploration run trace."""
    trace_id: str
    run_id: str
    task_description: str
    mutation_applied: Optional[str] = None
    spans: list[TraceSpan] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    exit_code: str = "unknown"

    def add_span(self, name: str, attributes: Optional[dict] = None) -> TraceSpan:
        """Add a new span to this trace."""
        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            name=name,
            start_time=datetime.now().isoformat(),
            attributes=attributes or {},
        )
        self.spans.append(span)
        return span

    def close_span(self, span: TraceSpan, status: str = "OK") -> None:
        """Close a span with end time and status."""
        span.end_time = datetime.now().isoformat()
        span.status = status

    def finalize(self, exit_code: str) -> None:
        """Finalize the trace context."""
        self.end_time = datetime.now().isoformat()
        self.exit_code = exit_code


class PhoenixTracer:
    """
    Tracer that collects spans for Phoenix analysis.

    In production, this would use OpenTelemetry exporters to send
    traces to Phoenix. For MVP, we collect in-memory and export
    to Phoenix-compatible format.
    """

    def __init__(self, project_name: str = "janus-labs"):
        """
        Initialize tracer.

        Args:
            project_name: Name for Phoenix project grouping
        """
        self.project_name = project_name
        self.traces: list[TraceContext] = []
        self._active_context: Optional[TraceContext] = None

    def start_trace(
        self,
        task_description: str,
        mutation: Optional[str] = None,
    ) -> TraceContext:
        """
        Start a new trace for an exploration run.

        Args:
            task_description: The task being executed
            mutation: Optional mutation strategy applied

        Returns:
            TraceContext for this run
        """
        context = TraceContext(
            trace_id=str(uuid.uuid4()),
            run_id=str(uuid.uuid4()),
            task_description=task_description,
            mutation_applied=mutation,
        )
        self.traces.append(context)
        self._active_context = context
        return context

    def get_active_context(self) -> Optional[TraceContext]:
        """Get the currently active trace context."""
        return self._active_context

    def end_trace(self, exit_code: str = "success") -> None:
        """End the active trace."""
        if self._active_context:
            self._active_context.finalize(exit_code)
            self._active_context = None

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        result: Any,
        duration_ms: int,
    ) -> None:
        """
        Record a tool invocation as a span.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            result: Tool result
            duration_ms: Execution duration
        """
        if not self._active_context:
            return

        span = self._active_context.add_span(
            name=f"tool:{tool_name}",
            attributes={
                "tool.name": tool_name,
                "tool.arguments": str(arguments),
                "tool.result": str(result)[:500],
                "tool.duration_ms": duration_ms,
            },
        )
        self._active_context.close_span(span)

    def record_message(self, role: str, content: str) -> None:
        """
        Record a conversation message as a span.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        if not self._active_context:
            return

        span = self._active_context.add_span(
            name=f"message:{role}",
            attributes={
                "message.role": role,
                "message.content": content[:1000],
            },
        )
        self._active_context.close_span(span)

    def export_traces(self) -> list[dict]:
        """
        Export traces in Phoenix-compatible format.

        Returns:
            List of trace dictionaries
        """
        return [
            {
                "trace_id": ctx.trace_id,
                "run_id": ctx.run_id,
                "task": ctx.task_description,
                "mutation": ctx.mutation_applied,
                "start_time": ctx.start_time,
                "end_time": ctx.end_time,
                "exit_code": ctx.exit_code,
                "spans": [
                    {
                        "span_id": span.span_id,
                        "name": span.name,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "attributes": span.attributes,
                        "status": span.status,
                    }
                    for span in ctx.spans
                ],
            }
            for ctx in self.traces
        ]

    def get_trace_count(self) -> int:
        """Return number of collected traces."""
        return len(self.traces)
