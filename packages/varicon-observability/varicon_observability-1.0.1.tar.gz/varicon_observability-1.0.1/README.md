# Varicon Observability

Unified observability package for logs, traces, and metrics across all Varicon services.

## Features

- **Universal Log Capture**: Captures all logs regardless of how they're created
- **Distributed Tracing**: Automatic trace correlation across services
- **Metrics**: System telemetry and performance metrics
- **Zero Code Changes**: Works with existing logging code
- **Framework Support**: Auto-detects and instruments Django, FastAPI, Celery

## Installation

### From Local Source (Development)

```bash
cd varicon_observability
pip install -e .

# Or with optional dependencies
pip install -e ".[full]"
```

### From Git Repository

```bash
pip install git+https://github.com/your-org/varicon-observability.git

# With optional dependencies
pip install "git+https://github.com/your-org/varicon-observability.git#egg=varicon-observability[full]"
```

### Build and Install from Source

```bash
cd varicon_observability
python -m build
pip install dist/varicon_observability-*.whl
```

### Installation Options

- **Basic**: `pip install varicon-observability`
- **Django**: `pip install varicon-observability[django]`
- **FastAPI**: `pip install varicon-observability[fastapi]`
- **Celery**: `pip install varicon-observability[celery]`
- **Full**: `pip install varicon-observability[full]`

## Quick Start

### Django (varicon)

```python
# varicon/varicon/asgi.py or settings.py
from varicon_observability import setup_observability

setup_observability(service_name="varicon-django")
```

### FastAPI (integrations_service)

```python
# integrations_service/main.py
from varicon_observability import setup_observability

setup_observability(service_name="integration-service")
```

## Configuration

Set environment variables:

```bash
OTEL_ENABLED=true
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz-otel-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=grpc  # or http
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=your-key
```

## What Gets Captured

- All Python logging (`logging.getLogger()`, `IntegrationLogger()`, etc.)
- Framework logs (Django, FastAPI, Uvicorn, Celery)
- HTTP requests (requests, httpx)
- Database queries (PostgreSQL via psycopg2)
- Redis operations
- Custom traces and metrics

**Note**: SQLAlchemy logs are disabled by default (set `ENABLE_SQLALCHEMY_LOGS=true` to enable)

## Architecture

```
Application Code
    ↓
Python Logging (any pattern)
    ↓
Root Logger Handler
    ↓
OpenTelemetry LoggingHandler
    ↓
OTLP Exporter
    ↓
SigNoz
```

All logs automatically include trace context for correlation.
