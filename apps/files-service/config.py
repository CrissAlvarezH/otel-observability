import os

AWS_REGION = os.getenv("AWS_REGION")
AUTH_DOMAIN = os.getenv("AUTH_DOMAIN")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
OTLP_COLLECTOR_ENDPOINT = os.getenv("OTLP_COLLECTOR_ENDPOINT")
FILES_TABLE = "otel-observability-files"
