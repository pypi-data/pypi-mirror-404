import logging
from typing import Optional
from .config import ObservabilityConfig

logger = logging.getLogger(__name__)

_initialized = False

def setup_observability(
    service_name: Optional[str] = None,
    enable_traces: bool = True,
    enable_metrics: bool = True,
    enable_logs: bool = True,
    instrument_framework: bool = True,
) -> bool:
    global _initialized
    
    if _initialized:
        return True
    
    if service_name:
        ObservabilityConfig.OTEL_SERVICE_NAME = service_name
    
    if not ObservabilityConfig.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return False
    
    if not ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return False
    
    # Try importing OpenTelemetry modules
    try:
        from .traces import setup_tracing
        from .metrics import setup_metrics
        from .logs import setup_logging, attach_log_handlers
        from .capture import ensure_all_logs_captured
    except ImportError as e:
        logger.warning(f"OpenTelemetry not installed: {e}. Observability disabled.")
        return False
    
    success = True
    
    if enable_traces:
        success &= setup_tracing(filter_database_spans=ObservabilityConfig.OTEL_FILTER_DATABASE_SPANS)
    
    if enable_metrics:
        success &= setup_metrics()
    
    if enable_logs:
        if setup_logging():
            attach_log_handlers()
            ensure_all_logs_captured()
    
    if instrument_framework:
        _instrument_framework()
    
    _initialized = True
    return success

def _instrument_framework():
    try:
        from .integrations import setup_django, setup_fastapi, setup_celery
        
        if setup_django():
            return
        
        if setup_fastapi():
            return
        
        setup_celery()
    except ImportError as e:
        logger.warning(f"Failed to instrument framework: {e}")

def setup_celery_observability(
    service_name: str = "integration-service-celery",
    logger_class=None,
) -> bool:
    """
    Complete observability setup for Celery workers.
    
    This function combines:
    1. General observability setup (traces, metrics, logs)
    2. Celery-specific instrumentation for trace context propagation
    
    Args:
        service_name: Name of the service for OpenTelemetry
        logger_class: Optional logger class with set_tenant_id method
        
    Returns:
        True if setup was successful, False otherwise
        
    Example:
        from integration_management.varicon_observability import setup_celery_observability
        from integration_management.common.logger import IntegrationLogger
        
        setup_celery_observability(logger_class=IntegrationLogger)
    """
    # First, set up general observability
    observability_enabled = setup_observability(
        service_name=service_name,
        enable_traces=True,
        enable_metrics=True,
        enable_logs=True,
        instrument_framework=True,
    )
    
    if not observability_enabled:
        logger.warning("Varicon Observability disabled or failed to initialize for Celery worker")
        return False
    
    logger.info("Varicon Observability initialized for Celery worker")
    
    # Then, set up Celery-specific instrumentation
    try:
        from .celery_instrumentation import setup_celery_instrumentation
        
        setup_celery_instrumentation(logger_class=logger_class)
        logger.info("Celery trace context propagation configured")
        return True
    except Exception as e:
        logger.warning(f"Failed to setup Celery instrumentation: {e}")
        return False

