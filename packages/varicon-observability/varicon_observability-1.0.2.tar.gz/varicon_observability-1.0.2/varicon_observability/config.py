import os
from typing import Optional

class ObservabilityConfig:
    OTEL_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "varicon-service")
    OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    OTEL_EXPORTER_OTLP_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    OTEL_EXPORTER_OTLP_PROTOCOL = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    OTEL_DEPLOYMENT_ENVIRONMENT = os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "production")
    
    # Span filtering configuration
    OTEL_FILTER_DATABASE_SPANS = os.getenv("OTEL_FILTER_DATABASE_SPANS", "true").lower() == "true"
    OTEL_FILTER_REDIS_SPANS = os.getenv("OTEL_FILTER_REDIS_SPANS", "false").lower() == "true"
    
    @classmethod
    def parse_headers(cls) -> dict:
        if not cls.OTEL_EXPORTER_OTLP_HEADERS:
            return {}
        headers = {}
        for header in cls.OTEL_EXPORTER_OTLP_HEADERS.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
        return headers
