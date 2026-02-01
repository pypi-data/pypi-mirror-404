import logging
from typing import Optional
from fastapi import FastAPI
from .config import ObservabilityConfig

logger = logging.getLogger(__name__)

def setup_django():
    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        
        # Always instrument Django
        DjangoInstrumentor().instrument()
        
        # Only instrument Psycopg2 if we're not filtering database spans
        # or if we explicitly want to see them for debugging
        if not ObservabilityConfig.OTEL_FILTER_DATABASE_SPANS:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            Psycopg2Instrumentor().instrument()
            logger.info("Django and PostgreSQL instrumentation enabled")
        else:
            logger.info("Django instrumentation enabled (PostgreSQL spans will be filtered)")
        
        return True
    except Exception as e:
        logger.warning(f"Django instrumentation failed: {e}")
        return False

def setup_postgres():
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        Psycopg2Instrumentor().instrument()
        logger.info("PostgreSQL instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"PostgreSQL instrumentation failed: {e}")
        return False

def setup_fastapi(app: Optional[FastAPI] = None):
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        
        if app:
            FastAPIInstrumentor().instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        logger.info("FastAPI instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")
        return False

def setup_celery():
    """
    Celery instrumentation is handled by our custom celery_instrumentation.py
    which properly handles tenant_id propagation and trace context.
    
    The built-in CeleryInstrumentor is disabled to avoid conflicts.
    """
    # NOTE: We use custom instrumentation from celery_instrumentation.py instead
    # of the built-in CeleryInstrumentor to properly handle tenant_id and
    # ensure trace context is correctly attached for logging.
    logger.info("Celery instrumentation delegated to custom celery_instrumentation module")
    return True


def instrument_asgi(application):
    """
    Wrap an ASGI application with OpenTelemetry middleware.
    
    Args:
        application: The ASGI application to instrument
        
    Returns:
        The instrumented application, or the original if instrumentation fails
    """
    if not ObservabilityConfig.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled, skipping ASGI instrumentation")
        return application
    
    try:
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
        
        instrumented = OpenTelemetryMiddleware(application)
        logger.info("ASGI instrumentation enabled via OpenTelemetryMiddleware")
        return instrumented
    except ImportError:
        logger.warning("OpenTelemetry ASGI instrumentation not available")
        return application
    except Exception as e:
        logger.warning(f"ASGI instrumentation failed: {e}")
        return application

