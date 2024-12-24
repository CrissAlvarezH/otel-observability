import os

AWS_REGION = 'us-east-1'
AUTH_DOMAIN = os.getenv("AUTH_DOMAIN")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')