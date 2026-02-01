import logging
from opentelemetry.sdk._logs import LoggingHandler
from opentelemetry._logs import get_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from .filters import NoisyLoggerFilter

def ensure_all_logs_captured():
    provider = get_logger_provider()
    if not provider or not isinstance(provider, LoggerProvider):
        return
    
    root_logger = logging.getLogger()
    if any(isinstance(h, LoggingHandler) for h in root_logger.handlers):
        return
    
    handler = LoggingHandler(logger_provider=provider)
    handler.addFilter(NoisyLoggerFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    
    manager = logging.Logger.manager
    for logger_name in list(manager.loggerDict.keys()):
        try:
            lg = manager.loggerDict[logger_name]
            if isinstance(lg, logging.Logger):
                lg.propagate = True
        except Exception:
            pass
