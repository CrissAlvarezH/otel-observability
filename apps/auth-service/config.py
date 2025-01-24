import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
OTLP_COLLECTOR_ENDPOINT = os.getenv("OTLP_COLLECTOR_ENDPOINT")
AUTH_TABLE = "otel-observability-auth"
FILES_TABLE = "otel-observability-files"
