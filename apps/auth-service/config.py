import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
OTLP_SPAN_EXPORTER_ENDPOINT = os.getenv("OTLP_SPAN_EXPORTER_ENDPOINT")
AUTH_TABLE = "otel-observability-auth"
FILES_TABLE = "otel-observability-files"
