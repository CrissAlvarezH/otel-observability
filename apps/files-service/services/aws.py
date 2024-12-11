from typing import List
import boto3
import os

from pydantic import BaseModel

from config import AWS_REGION

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


class FilePart(BaseModel):
    PartNumber: int
    ETag: str


def init_upload(filename: str) -> str:
    s3 = boto3.client('s3', region_name=AWS_REGION)

    response = s3.create_multipart_upload(
        Bucket=BUCKET_NAME,
        Key=filename
    )
    return response['UploadId']


def get_presigned_url(filename: str, upload_id: str, part_number: int) -> str:
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


def complete_upload(filename: str, upload_id: str, parts: List[FilePart]):
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

