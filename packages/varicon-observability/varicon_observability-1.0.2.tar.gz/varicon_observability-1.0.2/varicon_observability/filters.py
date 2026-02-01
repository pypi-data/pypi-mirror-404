import logging

class NoisyLoggerFilter(logging.Filter):
    NOISY_LOGGERS = [
        "urllib3",
        "urllib3.connectionpool",
        "opentelemetry",
        "opentelemetry.sdk",
        "opentelemetry.exporter",
        "requests",
        "requests.packages.urllib3",
        "httpx",
        "botocore",
        "boto3",
    ]
    
    def filter(self, record):
        for noisy in self.NOISY_LOGGERS:
            if record.name.startswith(noisy):
                return False
        return True
