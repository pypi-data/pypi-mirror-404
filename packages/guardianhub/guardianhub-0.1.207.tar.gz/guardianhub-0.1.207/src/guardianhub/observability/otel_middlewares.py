from typing import Optional

from fastapi import Request
from opentelemetry import baggage
from opentelemetry import propagate, context
from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span

async def bind_otel_context(request: Request, call_next):
    # Extract TraceID + Baggage from incoming headers
    ctx = propagate.extract(request.headers)

    # Attach to current execution
    token = context.attach(ctx)
    try:
        return await call_next(request)
    finally:
        # Prevent context from leaking to the next request in the pool
        context.detach(token)


class BaggageToSpanProcessor(SpanProcessor):
    """
    Automatically copies selected baggage values into every span's attributes.
    This ensures metadata like session_id follows the entire execution path.
    """
    BAGGAGE_KEYS = ("user_id", "session_id", "conversation_id","tenant_id")

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        # parent_context is the context the span was created with
        for key in self.BAGGAGE_KEYS:
            value = baggage.get_baggage(key, parent_context)
            if value is not None:
                # Stamp the attribute on the span so it's searchable in Tempo/Langfuse
                span.set_attribute(f"ctx.{key}", str(value))

    def on_end(self, span: Span) -> None:
        pass