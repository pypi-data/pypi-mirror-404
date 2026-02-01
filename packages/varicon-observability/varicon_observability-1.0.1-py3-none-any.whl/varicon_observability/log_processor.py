"""Custom log processor to inject trace context into OpenTelemetry log records."""

import contextvars
import logging
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk._logs import LogRecord as OTelLogRecord
from opentelemetry.sdk._logs import LogRecordProcessor

# Import tenant_context from celery_helpers module
try:
    from varicon_observability.celery_helpers import tenant_context
except ImportError:
    # Fallback if import fails
    tenant_context = contextvars.ContextVar("tenant_id", default="unknown-tenant")


class TraceContextLogProcessor(LogRecordProcessor):
    """
    Injects trace context (trace_id, span_id) and tenant_id into OpenTelemetry log records.
    
    This processor runs AFTER the LoggingHandler creates the log record, so it can:
    1. Override trace_id/span_id if they weren't captured correctly
    2. Add tenant_id from context variable
    3. Add these as searchable attributes for SigNoz
    
    This is especially important for Celery tasks where the span might be
    set up in task_prerun but the LoggingHandler might miss it.
    """
    
    def emit(self, log_record: OTelLogRecord) -> None:
        """
        Process and emit a log record with injected trace context and tenant_id.
        
        Args:
            log_record: The OpenTelemetry log record to process
        """
        try:
            # Initialize or convert attributes to a mutable dict
            if log_record.attributes is None:
                log_record.attributes = {}
            elif not isinstance(log_record.attributes, dict):
                # Convert to dict if it's an immutable mapping
                try:
                    log_record.attributes = dict(log_record.attributes)
                except Exception:
                    log_record.attributes = {}
            
            # 1. Extract and add tenant_id from context variable
            tenant_id = self._get_tenant_id(log_record)
            if tenant_id and tenant_id != "unknown-tenant":
                log_record.attributes["tenant_id"] = tenant_id
            
            # 2. Get current span and inject/override trace context
            # This is critical for Celery tasks where the span is set in task_prerun
            span = trace.get_current_span()
            
            # Fallback: check if we are in a Celery task but lost context
            if not (span and span.get_span_context().is_valid):
                span = self._get_celery_span_fallback()
            
            if span is not None:
                span_context = span.get_span_context()
                if span_context is not None and span_context.is_valid:
                    # Check if we have a valid trace (not zeros)
                    if span_context.trace_id != 0 and span_context.span_id != 0:
                        trace_id_hex = format(span_context.trace_id, "032x")
                        span_id_hex = format(span_context.span_id, "016x")
                        
                        # Add as attributes for SigNoz filtering
                        log_record.attributes["trace_id"] = trace_id_hex
                        log_record.attributes["span_id"] = span_id_hex
                        log_record.attributes["trace_flags"] = int(span_context.trace_flags)
                        
                        # ALSO override the log record's direct fields
                        # This ensures the trace context is in the standard OTLP fields
                        # even if LoggingHandler didn't capture it correctly
                        log_record.trace_id = span_context.trace_id
                        log_record.span_id = span_context.span_id
                        log_record.trace_flags = span_context.trace_flags
            
            # 3. Check if we still don't have trace context but the record has it
            # (in case LoggingHandler captured it but we need to add to attributes)
            if "trace_id" not in log_record.attributes:
                if hasattr(log_record, 'trace_id') and log_record.trace_id and log_record.trace_id != 0:
                    log_record.attributes["trace_id"] = format(log_record.trace_id, "032x")
                if hasattr(log_record, 'span_id') and log_record.span_id and log_record.span_id != 0:
                    log_record.attributes["span_id"] = format(log_record.span_id, "016x")
                    
        except Exception:
            # Silently ignore errors to avoid recursion and logging failures
            pass
    
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
    
    def _get_tenant_id(self, log_record: OTelLogRecord) -> Optional[str]:
        """
        Extract tenant_id from context variable or log message.
        
        Args:
            log_record: The log record to extract tenant_id from
            
        Returns:
            The tenant_id string or None if not found
        """
        # First try the context variable (most reliable for Celery tasks)
        try:
            tenant_id = tenant_context.get()
            if tenant_id and tenant_id != "unknown-tenant":
                return str(tenant_id)
        except Exception:
            pass
        
        # Fallback: try to extract from existing attributes
        try:
            if log_record.attributes and "tenant_id" in log_record.attributes:
                return str(log_record.attributes["tenant_id"])
        except Exception:
            pass
        
        # Final fallback: try to extract from log message
        try:
            if hasattr(log_record, 'body') and log_record.body:
                body_str = str(log_record.body)
                if 'Tenant:' in body_str:
                    tenant_part = body_str.split('Tenant:')[1].split(']')[0].strip()
                    if tenant_part and tenant_part != 'unknown-tenant':
                        return tenant_part
        except Exception:
            pass
        
        return None
    
    def shutdown(self) -> None:
        """Shutdown the processor. No resources to clean up."""
        pass
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered log records. No-op since we don't buffer."""
        return True
