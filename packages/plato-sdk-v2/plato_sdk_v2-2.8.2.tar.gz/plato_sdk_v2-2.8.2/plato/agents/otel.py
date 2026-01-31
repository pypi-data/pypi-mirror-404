"""OpenTelemetry integration for Plato agents and worlds.

Provides tracing utilities using OpenTelemetry SDK. Traces are sent directly
to the Chronos OTLP endpoint.

Usage:
    from plato.agents.otel import init_tracing, get_tracer, shutdown_tracing

    # Initialize tracing (sends to Chronos OTLP endpoint)
    init_tracing(
        service_name="my-world",
        session_id="session-123",
        otlp_endpoint="http://chronos/api/otel",
    )

    # Create spans
    tracer = get_tracer()
    with tracer.start_as_current_span("my-operation") as span:
        span.set_attribute("key", "value")
        # ... do work ...

    # Cleanup
    shutdown_tracing()
"""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.trace import Tracer

_module_logger = logging.getLogger(__name__)

# Global state
_tracer_provider = None
_initialized = False
_log_handler = None


class OTelSpanLogHandler(logging.Handler):
    """Logging handler that creates OTel spans for log messages.

    Converts Python log records to OTel spans with log attributes.
    """

    def __init__(self, tracer: Tracer, level: int = logging.INFO):
        super().__init__(level)
        self.tracer = tracer

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record as an OTel span."""
        try:
            # Debug: print that we're emitting a log span
            print(f"[OTel] Emitting log span: {record.name} - {record.getMessage()[:100]}")
            # Create a span for the log message
            with self.tracer.start_as_current_span(f"log.{record.levelname.lower()}") as span:
                span.set_attribute("log.level", record.levelname)
                span.set_attribute("log.message", record.getMessage())
                span.set_attribute("log.logger", record.name)
                span.set_attribute("source", "world")
                span.set_attribute("content", record.getMessage()[:1000])

                if record.funcName:
                    span.set_attribute("log.function", record.funcName)
                if record.lineno:
                    span.set_attribute("log.lineno", record.lineno)

                # Mark errors
                if record.levelno >= logging.ERROR:
                    span.set_attribute("error", True)

        except Exception:
            # Don't let logging errors crash the application
            pass


def init_tracing(
    service_name: str,
    session_id: str,
    otlp_endpoint: str,
    parent_trace_id: str | None = None,
    parent_span_id: str | None = None,
) -> None:
    """Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service (e.g., world name or agent name)
        session_id: Chronos session ID (added as resource attribute)
        otlp_endpoint: Chronos OTLP endpoint (e.g., http://chronos/api/otel)
        parent_trace_id: Optional parent trace ID for linking (hex string)
        parent_span_id: Optional parent span ID for linking (hex string)
    """
    global _tracer_provider, _initialized, _log_handler

    if _initialized:
        _module_logger.debug("Tracing already initialized")
        return

    try:
        from opentelemetry import context as context_api
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

        # Create resource with session ID
        resource = Resource.create(
            {
                "service.name": service_name,
                "plato.session.id": session_id,
            }
        )

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Add OTLP exporter pointing to Chronos (use SimpleSpanProcessor for immediate export)
        otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces")
        _tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # If parent context is provided, set it as the current context
        # This allows new spans to automatically link to the parent
        if parent_trace_id and parent_span_id:
            parent_context = SpanContext(
                trace_id=int(parent_trace_id, 16),
                span_id=int(parent_span_id, 16),
                is_remote=True,
                trace_flags=TraceFlags(0x01),  # Sampled
            )
            parent_span = NonRecordingSpan(parent_context)
            ctx = trace.set_span_in_context(parent_span)
            context_api.attach(ctx)
            print(f"[OTel] Using parent context: trace_id={parent_trace_id}, span_id={parent_span_id}")

        # Add OTel logging handler to capture logs from plato SDK
        tracer = trace.get_tracer(service_name)
        _log_handler = OTelSpanLogHandler(tracer, level=logging.INFO)

        # Add handler to plato loggers (worlds and agents)
        # Set level to INFO to ensure logs propagate from child loggers
        plato_logger = logging.getLogger("plato")
        plato_logger.setLevel(logging.INFO)
        plato_logger.addHandler(_log_handler)
        print(
            f"[OTel] Added log handler to 'plato' logger (level={plato_logger.level}, handlers={len(plato_logger.handlers)})"
        )

        _initialized = True

        print(f"[OTel] Tracing initialized: service={service_name}, session={session_id}, endpoint={otlp_endpoint}")

    except ImportError as e:
        print(f"[OTel] OpenTelemetry SDK not installed: {e}")
        _module_logger.warning(f"OpenTelemetry SDK not installed: {e}")
    except Exception as e:
        print(f"[OTel] Failed to initialize tracing: {e}")
        _module_logger.error(f"Failed to initialize tracing: {e}")


def shutdown_tracing(timeout_millis: int = 30000) -> None:
    """Shutdown the tracer provider and flush spans.

    Args:
        timeout_millis: Timeout in milliseconds to wait for flush (default 30s)
    """
    global _tracer_provider, _initialized, _log_handler

    # Remove log handler
    if _log_handler:
        try:
            plato_logger = logging.getLogger("plato")
            plato_logger.removeHandler(_log_handler)
        except Exception:
            pass
        _log_handler = None

    if _tracer_provider:
        try:
            # Force flush all pending spans before shutdown
            print(f"[OTel] Flushing spans (timeout={timeout_millis}ms)...")
            flush_success = _tracer_provider.force_flush(timeout_millis=timeout_millis)
            if flush_success:
                print("[OTel] Span flush completed successfully")
            else:
                print("[OTel] Span flush timed out or failed")

            _tracer_provider.shutdown()
            print("[OTel] Tracing shutdown complete")
        except Exception as e:
            print(f"[OTel] Error shutting down tracer: {e}")
            _module_logger.warning(f"Error shutting down tracer: {e}")

    _tracer_provider = None
    _initialized = False


def get_tracer(name: str = "plato") -> Tracer:
    """Get a tracer instance.

    Args:
        name: Tracer name (default: "plato")

    Returns:
        OpenTelemetry Tracer
    """
    return trace.get_tracer(name)


def is_initialized() -> bool:
    """Check if OTel tracing is initialized."""
    return _initialized


def instrument(service_name: str = "plato-agent") -> Tracer:
    """Initialize OTel tracing from environment variables.

    Reads the following env vars:
    - OTEL_EXPORTER_OTLP_ENDPOINT: Chronos OTLP endpoint (required for tracing)
    - SESSION_ID: Chronos session ID (default: "local")
    - OTEL_TRACE_ID: Parent trace ID for linking spans (optional)
    - OTEL_PARENT_SPAN_ID: Parent span ID for linking spans (optional)

    If OTEL_EXPORTER_OTLP_ENDPOINT is not set, returns a no-op tracer.

    Args:
        service_name: Name of the service for traces

    Returns:
        OpenTelemetry Tracer
    """
    import os

    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    session_id = os.environ.get("SESSION_ID", "local")
    parent_trace_id = os.environ.get("OTEL_TRACE_ID")
    parent_span_id = os.environ.get("OTEL_PARENT_SPAN_ID")

    print(f"[OTel] instrument() called: service={service_name}, endpoint={otel_endpoint}, session={session_id}")

    if not otel_endpoint:
        # Return default tracer (no-op if no provider configured)
        print("[OTel] No OTEL_EXPORTER_OTLP_ENDPOINT set, returning no-op tracer")
        return trace.get_tracer(service_name)

    # Initialize tracing with parent context if provided
    init_tracing(
        service_name=service_name,
        session_id=session_id,
        otlp_endpoint=otel_endpoint,
        parent_trace_id=parent_trace_id,
        parent_span_id=parent_span_id,
    )

    return trace.get_tracer(service_name)
