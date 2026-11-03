
"""OpenTelemetry tracing configuration for AI-A01."""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


_configured = False


def configure_tracing():
    """Configure console tracing and HTTPX instrumentation once."""
    global _configured

    if _configured:
        return trace.get_tracer("ai-a01.agent")

    resource = Resource.create({
        "service.name": "ai-a01-enterprise-agent",
        "service.version": "0.1.0",
    })

    provider = TracerProvider(resource=resource)

    provider.add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )

    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()

    _configured = True

    return trace.get_tracer("ai-a01.agent")


def get_tracer():
    """Return the AI-A01 tracer."""
    return trace.get_tracer("ai-a01.agent")


from functools import wraps
from opentelemetry.trace import Status, StatusCode


def traced_node(node_name):
    """Add an OpenTelemetry span around a LangGraph node."""

    def decorator(func):
        @wraps(func)
        def wrapper(state):
            tracer = get_tracer()

            with tracer.start_as_current_span(
                f"agent.{node_name}"
            ) as span:
                span.set_attribute("agent.node", node_name)

                try:
                    result = func(state)

                    if node_name == "authorize":
                        span.set_attribute(
                            "authorization.allowed",
                            result.get("authorized", False),
                        )

                    elif node_name == "retrieve_orders":
                        span.set_attribute(
                            "orders.count",
                            len(result.get("orders", [])),
                        )

                    elif node_name == "retrieve_policies":
                        span.set_attribute(
                            "policies.count",
                            len(result.get("policies", [])),
                        )

                    elif node_name == "validate":
                        span.set_attribute(
                            "validation.passed",
                            result.get("validated", False),
                        )

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as exc:
                    span.set_attribute(
                        "error.type",
                        type(exc).__name__,
                    )
                    span.set_status(
                        Status(StatusCode.ERROR, "Node execution failed")
                    )
                    raise

        return wrapper

    return decorator
