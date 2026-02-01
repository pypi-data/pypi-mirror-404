"""Celery instrumentation for OpenTelemetry trace and log context propagation."""

import logging
import contextvars
from typing import Any, Optional
from celery.signals import task_prerun, task_postrun, before_task_publish
from opentelemetry import trace, context as otel_context
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Store context tokens for cleanup
_context_tokens = {}

# Import tenant_context from celery_helpers module for setting tenant_id
try:
    from varicon_observability.celery_helpers import tenant_context
except ImportError:
    # Fallback if import fails - create local context var
    tenant_context = contextvars.ContextVar("tenant_id", default="unknown-tenant")


def _extract_tenant_id_from_args(args, kwargs) -> Optional[str]:
    """
    Extract tenant_id from task arguments.
    
    Handles various argument patterns:
    - args[1] as tenant_id (most common)
    - kwargs['tenant_id']
    - kwargs['tenant']
    """
    tenant_id = None
    
    # Try kwargs first
    if kwargs:
        tenant_id = kwargs.get('tenant_id') or kwargs.get('tenant')
    
    # Try args[1] as fallback (common pattern in this codebase)
    if not tenant_id and args and len(args) >= 2:
        potential_tenant = args[1]
        # Validate it looks like a tenant_id (UUID-like or string)
        if potential_tenant and isinstance(potential_tenant, (str, int)):
            tenant_id = str(potential_tenant)
    
    return tenant_id


def setup_celery_instrumentation(logger_class=None):
    """
    Set up Celery instrumentation for trace context propagation.
    
    This function registers signal handlers that:
    1. Inject trace context when publishing tasks (before_task_publish)
    2. Extract trace context when tasks start (task_prerun)
    3. Set tenant_id in logger context
    4. Clean up context when tasks complete (task_postrun)
    
    Args:
        logger_class: Optional logger class with set_tenant_id method
    """
    
    @before_task_publish.connect(weak=False)
    def inject_trace_context_on_publish(sender=None, headers=None, body=None, **kwargs):
        """Inject trace context into task headers before publishing."""
        if headers is not None:
            # Inject current trace context using W3C TraceContext format
            inject(headers)
            
            # Also inject tenant_id if available
            try:
                current_tenant = tenant_context.get()
                if current_tenant and current_tenant != "unknown-tenant":
                    headers['x-tenant-id'] = str(current_tenant)
            except Exception:
                pass
            
            # Log for debugging
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                logger.debug(f"[OTEL_CELERY] Injected trace_id {trace_id} into task {sender}, headers: {list(headers.keys())}")
    
    @task_prerun.connect(weak=False)
    def extract_trace_context_on_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
        """Extract trace context from task headers and set as current."""
        try:
            # Initialize token storage for this task
            _context_tokens[task_id] = {}
            
            # Get headers from task.request (the correct way in Celery)
            headers = {}
            if task and hasattr(task, 'request'):
                headers = task.request.get('headers') or {}
                # Also check for direct header attributes
                if not headers and hasattr(task.request, 'headers'):
                    headers = task.request.headers or {}
            
            logger.debug(f"[OTEL_CELERY] Task {task.name if task else 'unknown'} headers: {list(headers.keys()) if headers else 'none'}")
            
            # Extract tenant_id from headers or args
            tenant_id = None
            if headers and 'x-tenant-id' in headers:
                tenant_id = headers['x-tenant-id']
            
            if not tenant_id:
                tenant_id = _extract_tenant_id_from_args(args, kwargs or {})
            
            # Set tenant_id in context variable AND logger class
            if tenant_id:
                tenant_context.set(str(tenant_id))
                if logger_class:
                    try:
                        logger_instance = logger_class()
                        logger_instance.set_tenant_id(str(tenant_id))
                    except Exception as e:
                        logger.debug(f"[OTEL_CELERY] Could not set tenant via logger_class: {e}")
            
            # Extract trace context from headers and create span
            tracer = trace.get_tracer("varicon_observability.celery", "1.0.0")
            
            if headers:
                # Extract the parent context from headers
                parent_context = extract(headers)
                
                # Log what we extracted
                parent_span = trace.get_current_span(parent_context)
                if parent_span and parent_span.get_span_context().is_valid:
                    parent_ctx = parent_span.get_span_context()
                    parent_trace_id = format(parent_ctx.trace_id, "032x")
                    logger.info(f"[OTEL_CELERY] Extracted parent trace_id {parent_trace_id} from headers for task {task.name if task else 'unknown'}")
                
                # Start a new span as child of the extracted context
                # Using start_as_current_span equivalent manually
                span = tracer.start_span(
                    name=f"celery.task.execute",
                    context=parent_context,  # Parent context from headers
                    kind=SpanKind.CONSUMER,
                    attributes={
                        "celery.task_id": str(task_id),
                        "celery.task_name": task.name if task else "unknown",
                        "messaging.system": "celery",
                        "messaging.operation": "process",
                    }
                )
            else:
                # No headers - create a new root span
                logger.warning(f"[OTEL_CELERY] No headers found for task {task.name if task else 'unknown'}, creating root span")
                span = tracer.start_span(
                    name=f"celery.task.execute",
                    kind=SpanKind.CONSUMER,
                    attributes={
                        "celery.task_id": str(task_id),
                        "celery.task_name": task.name if task else "unknown",
                        "messaging.system": "celery",
                        "messaging.operation": "process",
                    }
                )
            
            # Add tenant_id as span attribute if available
            if tenant_id:
                span.set_attribute("tenant_id", str(tenant_id))
            
            # Create a new context with this span and attach it to make it CURRENT
            # This is the critical step - we must attach the context!
            new_context = trace.set_span_in_context(span)
            context_token = otel_context.attach(new_context)
            
            # Store span, token, AND context for cleanup and async access
            _context_tokens[task_id]['span'] = span
            _context_tokens[task_id]['context_token'] = context_token
            _context_tokens[task_id]['context'] = new_context  # Store context for async tasks
            
            # Verify the span is now current
            current_span = trace.get_current_span()
            if current_span and current_span.get_span_context().is_valid:
                ctx = current_span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                logger.info(f"[OTEL_CELERY] ✓ Task {task.name if task else 'unknown'} trace_id: {trace_id}, span_id: {span_id}, tenant_id: {tenant_id}")
            else:
                logger.warning(f"[OTEL_CELERY] ✗ Span not current after attach for task {task.name if task else 'unknown'}")
                
        except Exception as e:
            logger.warning(f"[OTEL_CELERY] Failed to extract trace context: {e}", exc_info=True)
    
    @task_postrun.connect(weak=False)
    def cleanup_trace_context_on_postrun(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
        """Clean up trace context after task completion."""
        try:
            if task_id in _context_tokens:
                tokens = _context_tokens[task_id]
                
                # End span if it exists
                if 'span' in tokens:
                    span = tokens['span']
                    # Set span status based on task state
                    if state == 'SUCCESS':
                        span.set_status(Status(StatusCode.OK))
                    elif state in ('FAILURE', 'REVOKED'):
                        span.set_status(Status(StatusCode.ERROR, f"Task {state}"))
                    span.end()
                    logger.debug(f"[OTEL_CELERY] Ended span for task {task.name if task else 'unknown'}")
                
                # Detach context (this restores the previous context)
                if 'context_token' in tokens:
                    try:
                        otel_context.detach(tokens['context_token'])
                    except Exception:
                        pass
                
                # Reset tenant context
                try:
                    tenant_context.set("unknown-tenant")
                except Exception:
                    pass
                
                # Clean up stored tokens
                del _context_tokens[task_id]
                
        except Exception as e:
            logger.warning(f"[OTEL_CELERY] Failed to cleanup trace context: {e}")
    
    logger.info("Celery OpenTelemetry instrumentation configured with proper context attachment")
    return True
