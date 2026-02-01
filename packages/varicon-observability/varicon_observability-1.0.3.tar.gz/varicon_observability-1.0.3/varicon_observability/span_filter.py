"""Span processor to filter out unwanted spans (like database queries)."""

import logging
from typing import Optional
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
from opentelemetry.context import Context

logger = logging.getLogger(__name__)


class DatabaseSpanFilter(SpanProcessor):
    """
    A span processor that filters out database query spans.
    
    This processor prevents database query spans from being exported to the
    tracing backend (Signoz), keeping only HTTP/API and business logic spans.
    """
    
    # List of span names or patterns to filter out
    FILTERED_SPAN_PREFIXES = [
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "CREATE",
        "ALTER",
        "DROP",
        "TRUNCATE",
        # PostgreSQL specific
        "psycopg2",
        "postgres",
        # Django ORM specific
        "django.db",
    ]
    
    def __init__(self, next_processor: SpanProcessor):
        """
        Initialize the filter with a downstream processor.
        
        Args:
            next_processor: The actual span processor (e.g., BatchSpanProcessor)
                          that should receive non-filtered spans
        """
        self.next_processor = next_processor
    
    def on_start(
        self, 
        span: "Span", 
        parent_context: Optional[Context] = None
    ) -> None:
        """Called when a span starts."""
        # Forward to next processor if span should not be filtered
        if not self._should_filter(span):
            self.next_processor.on_start(span, parent_context)
    
    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends. Filter here before exporting."""
        if self._should_filter(span):
            # Don't forward to next processor - effectively drops the span
            logger.debug(f"Filtered database span: {span.name}")
            return
        
        # Forward to next processor for export
        self.next_processor.on_end(span)
    
    def shutdown(self) -> None:
        """Shutdown the processor."""
        self.next_processor.shutdown()
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush the processor."""
        return self.next_processor.force_flush(timeout_millis)
    
    def _should_filter(self, span) -> bool:
        """
        Determine if a span should be filtered out.
        
        Args:
            span: The span to check
            
        Returns:
            True if the span should be filtered (not exported), False otherwise
        """
        span_name = span.name if hasattr(span, 'name') else str(span)
        
        # Check if span name starts with any filtered prefix
        for prefix in self.FILTERED_SPAN_PREFIXES:
            if span_name.startswith(prefix):
                return True
        
        # Check span attributes for database-related attributes
        if hasattr(span, 'attributes'):
            attributes = span.attributes or {}
            
            # Filter by db.system attribute (added by DB instrumentors)
            if "db.system" in attributes:
                return True
            
            # Filter by db.statement attribute (SQL queries)
            if "db.statement" in attributes:
                return True
            
            # Filter by db.operation attribute
            if "db.operation" in attributes:
                return True
        
        return False


class SelectiveSpanFilter(SpanProcessor):
    """
    A more configurable span processor that can filter spans based on
    various criteria.
    """
    
    def __init__(
        self, 
        next_processor: SpanProcessor,
        filter_databases: bool = True,
        filter_redis: bool = False,
        custom_filters: Optional[list] = None
    ):
        """
        Initialize the filter.
        
        Args:
            next_processor: The actual span processor
            filter_databases: Whether to filter database query spans
            filter_redis: Whether to filter Redis query spans
            custom_filters: List of custom span name prefixes to filter
        """
        self.next_processor = next_processor
        self.filter_databases = filter_databases
        self.filter_redis = filter_redis
        self.custom_filters = custom_filters or []
    
    def on_start(
        self, 
        span: "Span", 
        parent_context: Optional[Context] = None
    ) -> None:
        """Called when a span starts."""
        if not self._should_filter(span):
            self.next_processor.on_start(span, parent_context)
    
    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends."""
        if self._should_filter(span):
            logger.debug(f"Filtered span: {span.name}")
            return
        
        self.next_processor.on_end(span)
    
    def shutdown(self) -> None:
        """Shutdown the processor."""
        self.next_processor.shutdown()
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush the processor."""
        return self.next_processor.force_flush(timeout_millis)
    
    def _should_filter(self, span) -> bool:
        """Determine if a span should be filtered."""
        if not hasattr(span, 'attributes'):
            return False
        
        attributes = span.attributes or {}
        
        # Filter database spans
        if self.filter_databases:
            if "db.system" in attributes or "db.statement" in attributes:
                return True
        
        # Filter Redis spans
        if self.filter_redis:
            if attributes.get("db.system") == "redis":
                return True
        
        # Filter custom patterns
        span_name = span.name if hasattr(span, 'name') else str(span)
        for pattern in self.custom_filters:
            if pattern in span_name:
                return True
        
        return False
