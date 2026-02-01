"""Helper utilities for Celery task invocation with trace and tenant context propagation."""

import logging
import contextvars
from typing import Any
from celery import Task
from opentelemetry.propagate import inject
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Local tenant context variable
# Note: If using IntegrationLogger, it should set this same context variable
tenant_context = contextvars.ContextVar("tenant_id", default="unknown-tenant")


def call_task_with_trace_context(
    task: Task,
    *args,
    queue: str = None,
    **kwargs
) -> Any:
    """
    Call a Celery task with OpenTelemetry trace context and tenant_id propagation.
    
    This function automatically injects the current trace context and tenant_id
    into task headers, ensuring that background tasks (Celery) share the same
    trace_id and tenant_id as the foreground request (Django/FastAPI).
    
    Args:
        task: The Celery task to invoke
        *args: Positional arguments to pass to the task
        queue: Optional queue name for the task
        **kwargs: Keyword arguments to pass to the task
        
    Returns:
        AsyncResult from the task invocation
        
    Example:
        from varicon_observability import call_task_with_trace_context
        
        # Instead of:
        my_task.delay(arg1, arg2)
        
        # Use:
        call_task_with_trace_context(my_task, arg1, arg2)
        
        # With queue:
        call_task_with_trace_context(my_task, arg1, queue="queue_A")
    """
    # Create a carrier dict to hold trace context
    carrier = {}
    
    # Inject current trace context into the carrier
    # This extracts trace_id, span_id from the current span
    inject(carrier)
    
    # Also inject tenant_id if available in context
    try:
        current_tenant = tenant_context.get()
        if current_tenant and current_tenant != "unknown-tenant":
            carrier['x-tenant-id'] = str(current_tenant)
            logger.info(f"[TRACE_INJECT] Injecting tenant_id {current_tenant} into task {task.name}")
    except Exception as e:
        logger.debug(f"[TRACE_INJECT] Could not inject tenant_id: {e}")
    
    # Log what we're injecting for debugging
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        trace_id = format(ctx.trace_id, "032x")
        logger.info(f"[TRACE_INJECT] Injecting trace_id {trace_id} into task {task.name}, headers: {list(carrier.keys())}")
    else:
        logger.warning(f"[TRACE_INJECT] No valid span context when calling task {task.name}")
    
    # Get existing headers from kwargs or create new dict
    headers = kwargs.pop('headers', {})
    
    # Merge trace context with any existing headers
    headers.update(carrier)
    
    # Build apply_async options
    apply_kwargs = {
        'args': args,
        'kwargs': kwargs,
        'headers': headers,
    }
    
    # Add queue if specified
    if queue:
        apply_kwargs['queue'] = queue
    
    # Call the task with trace context in headers
    return task.apply_async(**apply_kwargs)

