import logging
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from .config import ObservabilityConfig

logger = logging.getLogger(__name__)

_meter_provider = None

def setup_metrics() -> bool:
    global _meter_provider
    
    if not ObservabilityConfig.OTEL_ENABLED or not ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT:
        return False
    
    try:
        resource = Resource.create({
            "service.name": ObservabilityConfig.OTEL_SERVICE_NAME,
            "service.version": ObservabilityConfig.OTEL_SERVICE_VERSION,
            "deployment.environment": ObservabilityConfig.OTEL_DEPLOYMENT_ENVIRONMENT,
        })
        
        if ObservabilityConfig.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            endpoint = ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT
        else:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            # HTTP requires full path
            endpoint = ObservabilityConfig.OTEL_EXPORTER_OTLP_ENDPOINT
            if not endpoint.endswith("/v1/metrics"):
                endpoint = endpoint.rstrip("/") + "/v1/metrics"
        
        headers = ObservabilityConfig.parse_headers()
        exporter = OTLPMetricExporter(
            endpoint=endpoint,
            headers=headers if headers else None,
        )
        
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
        _meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(_meter_provider)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup metrics: {e}", exc_info=True)
        return False
