import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from .config import ObservabilityConfig

logger = logging.getLogger(__name__)

_tracer_provider = None

def setup_tracing(filter_database_spans: bool = True) -> bool:
    """
    Setup OpenTelemetry tracing with optional span filtering.
    
    Args:
        filter_database_spans: If True, filters out database query spans from traces.
                              Set to False to include all database queries in traces.
    
    Returns:
        True if setup was successful, False otherwise
    """
    global _tracer_provider
    
    if not ObservabilityConfig.OTEL_ENABLED or not ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT:
        return False
    
    try:
        resource = Resource.create({
            "service.name": ObservabilityConfig.OTEL_SERVICE_NAME,
            "service.version": ObservabilityConfig.OTEL_SERVICE_VERSION,
            "deployment.environment": ObservabilityConfig.OTEL_DEPLOYMENT_ENVIRONMENT,
        })
        
        existing = trace.get_tracer_provider()
        if existing and not isinstance(existing, trace.ProxyTracerProvider):
            _tracer_provider = existing
            return True
        
        _tracer_provider = TracerProvider(resource=resource)
        
        if ObservabilityConfig.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            endpoint = ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT
        else:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            # HTTP requires full path
            endpoint = ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT
            if not endpoint.endswith("/v1/traces"):
                endpoint = endpoint.rstrip("/") + "/v1/traces"
        
        headers = ObservabilityConfig.parse_headers()
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers if headers else None,
        )
        
        # Create batch processor
        batch_processor = BatchSpanProcessor(exporter)
        
        # Wrap with database span filter if enabled
        if filter_database_spans:
            from .span_filter import DatabaseSpanFilter
            span_processor = DatabaseSpanFilter(batch_processor)
            logger.info("Database span filtering enabled - DB queries will not appear in traces")
        else:
            span_processor = batch_processor
            logger.info("Database span filtering disabled - all spans will be traced")
        
        _tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(_tracer_provider)
        
        _instrument_libraries()
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}", exc_info=True)
        return False

def _instrument_libraries():
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
    except Exception:
        pass
    
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
    except Exception:
        pass
    
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except Exception:
        pass
