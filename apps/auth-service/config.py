import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
OTLP_SPAN_EXPORTER_ENDPOINT = os.getenv("OTLP_SPAN_EXPORTER_ENDPOINT")
