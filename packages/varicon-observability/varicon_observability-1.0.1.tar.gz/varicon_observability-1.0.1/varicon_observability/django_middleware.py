"""Django middleware for automatic trace context and tenant_id injection."""

import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Import tenant_context
try:
    from varicon_observability.celery_helpers import tenant_context
except ImportError:
    import contextvars
    tenant_context = contextvars.ContextVar("tenant_id", default="unknown-tenant")


class TraceContextMiddleware:
    """
    Django middleware that:
    1. Extracts tenant_id from request headers and sets it in context
    2. Creates a span for each HTTP request (for ASGI/Channels compatibility)
    3. Ensures all logs within the request have trace_id, span_id, and tenant_id
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.tracer = trace.get_tracer("varicon.django.middleware", "1.0.0")
    
    def __call__(self, request):
        # Extract tenant_id from request
        tenant_id = self._extract_tenant_id(request)
        
        # Set tenant_id in context variable FIRST
        if tenant_id:
            tenant_context.set(str(tenant_id))
        
        # Create a span for this request
        span_name = f"{request.method} {request.path}"
        
        with self.tracer.start_as_current_span(
            span_name,
            kind=trace.SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": request.get_full_path(),
                "http.scheme": request.scheme,
                "http.host": request.get_host(),
                "tenant_id": str(tenant_id) if tenant_id else "unknown",
            }
        ) as span:
            # Log span info for debugging
            ctx = span.get_span_context()
            if ctx.is_valid:
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                logger.debug(f"[TRACE_MIDDLEWARE] Request {span_name} trace_id: {trace_id}, span_id: {span_id}, tenant_id: {tenant_id}")
            
            # Process the request
            response = self.get_response(request)
            
            # Add response info to span
            if hasattr(response, 'status_code'):
                span.set_attribute("http.status_code", response.status_code)
            
            return response
    
    def _extract_tenant_id(self, request):
        """Extract tenant_id from request in order of priority."""
        # 1. Try request attribute (set by auth middleware)
        tenant_id = getattr(request, 'tenant_id', None)
        
        # 2. Try Tenant-Id header
        if not tenant_id:
            tenant_id = request.headers.get('Tenant-Id')
        
        # 3. Try X-Tenant-Id header
        if not tenant_id:
            tenant_id = request.headers.get('X-Tenant-Id')
        
        # 4. Try META (for WSGI compatibility)
        if not tenant_id:
            tenant_id = request.META.get('HTTP_TENANT_ID')
        
        return tenant_id
