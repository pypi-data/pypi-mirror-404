"""Logging filter to inject trace context into standard Python log records."""

import logging
from opentelemetry import trace
from typing import Optional


class TraceContextFilter(logging.Filter):
    """
    Adds trace context (trace_id, span_id) to standard Python log records.
    
    This filter extracts the current span context and injects trace_id and span_id
    into log records, making them available for log formatters and handlers.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Inject trace_id, span_id, and tenant_id into log record.
        
        Args:
            record: The Python log record to filter/modify
            
        Returns:
            True to allow the record to be logged
        """
        try:
            # 1. Inject tenant_id from context variable if not already set
            if not hasattr(record, 'tenant_id'):
                try:
                    from varicon_observability.celery_helpers import tenant_context
                    record.tenant_id = tenant_context.get()
                except Exception:
                    record.tenant_id = "unknown-tenant"
            
            # 2. Inject trace context (trace_id, span_id)
            span = trace.get_current_span()
            
            # Fallback: check if we are in a Celery task but lost context
            if not (span and span.get_span_context().is_valid):
                span = self._get_celery_span_fallback()
            
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                # Only set trace context if it's valid (not all zeros)
                if ctx.trace_id != 0 and ctx.span_id != 0:
                    record.trace_id = format(ctx.trace_id, "032x")
                    record.span_id = format(ctx.span_id, "016x")
                    record.trace_flags = ctx.trace_flags
                else:
                    # No valid trace context
                    record.trace_id = "-"
                    record.span_id = "-"
                    record.trace_flags = 0
            else:
                # No active span - use placeholder instead of zeros
                record.trace_id = "-"
                record.span_id = "-"
                record.trace_flags = 0
        except Exception:
            # Don't fail logging if trace context injection fails
            record.trace_id = "-"
            record.span_id = "-"
            record.trace_flags = 0
        
        return True

    def _get_celery_span_fallback(self) -> Optional[trace.Span]:
        """
        Attempt to retrieve the span from Celery task context if not in current context.
        This handles cases where context propagation fails in Celery workers.
        """
        try:
            from celery import current_task
            
            # Check if we are inside a Celery task
            if not current_task:
                return None
                
            # Get the task ID
            task_id = None
            if hasattr(current_task, 'request') and current_task.request:
                task_id = current_task.request.id
            
            if not task_id:
                return None
                
            # Try to retrieve the span from our custom instrumentation storage
            # Use lazy import to avoid circular dependencies
            from varicon_observability.celery_instrumentation import _context_tokens
            
            if task_id in _context_tokens:
                token_data = _context_tokens[task_id]
                if 'span' in token_data:
                    return token_data['span']
                    
            return None
            
        except ImportError:
            # Celery or instrumentation not available
            return None
        except Exception:
            # Safely ignore any other errors during fallback
            return None

