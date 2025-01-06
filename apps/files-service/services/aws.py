from typing import List

import boto3
from pydantic import BaseModel
from opentelemetry import trace

from config import AWS_REGION, SQS_QUEUE_URL, BUCKET_NAME


tracer = trace.get_tracer("files-service")

class FilePart(BaseModel):
    PartNumber: int
    ETag: str


@tracer.start_as_current_span("init_upload") 
def init_upload(filename: str) -> str:
    span = trace.get_current_span()
    span.set_attributes({
        "file.name": filename,
        "bucket.name": BUCKET_NAME,
    })

    s3 = boto3.client('s3', region_name=AWS_REGION)

    response = s3.create_multipart_upload(
        Bucket=BUCKET_NAME,
        Key=filename
    )
    id = response['UploadId']
    span.set_attribute("upload.id", id)
    return id


@tracer.start_as_current_span("get_presigned_url") 
def get_presigned_url(filename: str, upload_id: str, part_number: int) -> str:
    span = trace.get_current_span()
    span.set_attributes({
        "file.name": filename, "bucket.name": BUCKET_NAME,
        "upload.id": upload_id, "file.part_number": part_number, 
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


@tracer.start_as_current_span("complete_upload") 
def complete_upload(filename: str, upload_id: str, parts: List[FilePart]):
    span = trace.get_current_span()
    span.set_attributes({
        "file.name": filename, "bucket.name": BUCKET_NAME, "upload.id": upload_id,
    })

    s3 = boto3.client('s3', region_name=AWS_REGION)

    s3.complete_multipart_upload(
        Bucket=BUCKET_NAME,
        Key=filename,
        UploadId=upload_id,
        MultipartUpload={'Parts': [part.model_dump() for part in parts]},
    )


def list_multipart_uploads() -> list[str]:
    s3 = boto3.client('s3', region_name=AWS_REGION)

    return s3.list_multipart_uploads(Bucket=BUCKET_NAME)


@tracer.start_as_current_span("queue_uploaded_file") 
def queue_uploaded_file(file_id: str, file_name: str):
    span = trace.get_current_span()
    span.set_attributes({
        "file.id": file_id, "file.name": file_name, "queue.url": SQS_QUEUE_URL,
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
            },
            # attributes to create a link with the load pipeline
            "trace_id": {
                "DataType": "String",
                "StringValue": str(span.get_span_context().trace_id),
            },
            "span_id": {
                "DataType": "String",
                "StringValue": str(span.get_span_context().span_id),
            }
        }
    )
    if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to queue uploaded file")
    return res.get('MessageId')
