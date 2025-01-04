from typing import List

import boto3
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from config import AWS_REGION, SQS_QUEUE_URL, BUCKET_NAME


tracer = trace.get_tracer("files-service")

class FilePart(BaseModel):
    PartNumber: int
    ETag: str


def init_upload(filename: str) -> str:
    with tracer.start_as_current_span("init_upload") as span:
        try:
            span.set_attributes({
                "filename": filename,
                "bucket": BUCKET_NAME,
                "table": "otel-observability-files"
            })

            s3 = boto3.client('s3', region_name=AWS_REGION)

            response = s3.create_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=filename
            )
            return response['UploadId']
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def get_presigned_url(filename: str, upload_id: str, part_number: int) -> str:
    with tracer.start_as_current_span("get_presigned_url") as span:
        try:
            span.set_attributes({
                "filename": filename, "bucket": BUCKET_NAME, "upload_id": upload_id,
                "part_number": part_number, "table": "otel-observability-files"
            })

            s3 = boto3.client('s3', region_name=AWS_REGION)

            return s3.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': filename,
                    'UploadId': upload_id,
                    'PartNumber': part_number,
                },
                ExpiresIn=3600  # 1 hour
            )
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def complete_upload(filename: str, upload_id: str, parts: List[FilePart]):
    with tracer.start_as_current_span("complete_upload") as span:
        try:
            span.set_attributes({
                "filename": filename, "bucket": BUCKET_NAME, "upload_id": upload_id,
                "table": "otel-observability-files"
            })

            s3 = boto3.client('s3', region_name=AWS_REGION)

            s3.complete_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=filename,
                UploadId=upload_id,
                MultipartUpload={'Parts': [part.model_dump() for part in parts]},
            )
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def list_multipart_uploads() -> list[str]:
    s3 = boto3.client('s3', region_name=AWS_REGION)

    return s3.list_multipart_uploads(Bucket=BUCKET_NAME)


def queue_uploaded_file(file_id: str, file_name: str):
    with tracer.start_as_current_span("queue_uploaded_file") as span:
        try:
            span.set_attributes({
                "file_id": file_id, "file_name": file_name, "queue": SQS_QUEUE_URL,
                "table": "otel-observability-files"
            })

            sqs = boto3.client('sqs', region_name=AWS_REGION)
            res = sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody="file uploaded",
                MessageAttributes={
                    "file_id": {
                        "DataType": "String",
                        "StringValue": file_id,
                    },
                    "file_name": {
                        "DataType": "String",
                        "StringValue": file_name,
                    }
                }
            )
            if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                raise Exception("Failed to queue uploaded file")
            return res.get('MessageId')
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise e
