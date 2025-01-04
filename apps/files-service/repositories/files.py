from typing import List
from datetime import datetime
from ulid import ULID

import boto3
from pydantic import BaseModel, Field
from boto3.dynamodb.conditions import Key
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from config import AWS_REGION


tracer = trace.get_tracer(__name__)


class InsertFile(BaseModel):
    filename: str
    file_size: int
    status: str = Field(default='pending', description='pending, stored, loaded')
    row_count: int
    username: str
    columns: List[str]


class UpdateFile(BaseModel):
    status: str = Field(default='pending', description='pending, stored, loaded, failed')


class File(BaseModel):
    id: str
    creation_datetime: str
    filename: str
    file_size: int
    status: str = Field(default='pending', description='pending, stored, loaded')


def get_files(page_size: int = 10, last_id: str = None):
    with tracer.start_as_current_span("get_files") as span:
        try:
            # Add attributes to the span
            span.set_attributes({
                "page_size": page_size,
                "last_id": last_id or "None",
                "table": "otel-observability-files"
            })
            
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table('otel-observability-files')
            
            query_params = {
                'IndexName': 'creation_datetime-index',
                'KeyConditionExpression': Key('data_type').eq('FILE'), 
                'ScanIndexForward': False, # sort in descending order
                'Limit': page_size,
            }
            
            if last_id:
                query_params['ExclusiveStartKey'] = {'id': last_id, "data_type": "FILE"}
            
            rs = table.query(**query_params)
            
            # Add result information to span
            span.set_attributes({
                "result.count": len(rs.get('Items', [])),
                "result.has_more": 'LastEvaluatedKey' in rs
            })
            
            return {
                'items': rs.get('Items', []),
                'last_id': rs.get('LastEvaluatedKey', {}).get('id'),
                'has_more': 'LastEvaluatedKey' in rs
            }
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def insert_file(file: InsertFile) -> str:
    with tracer.start_as_current_span("insert_file") as span:
        try:
            span.set_attributes({
                "filename": file.filename,
                "file_size": file.file_size,
                "table": "otel-observability-files"
            })
            
            db = boto3.client('dynamodb', region_name=AWS_REGION)
            id = str(ULID())
            
            res = db.put_item(
                TableName='otel-observability-files',
                Item={
                    "id": {"S": id},
                    "filename": {"S": file.filename},
                    "file_size": {"N": str(file.file_size)},
                    "status": {"S": file.status},
                    "username": {"S": file.username},
                    "columns": {"L": [{"S": col} for col in file.columns]},
                    # data_type is an artificial attribute to "hack" dynamodb 
                    # because its required add a hash key in GlobalSecondaryIndexes
                    "data_type": {"S": "FILE"}, 
                    "creation_datetime": {"S": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    "row_count": {"N": str(file.row_count)},
                }
            )
            if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                raise Exception("Failed to insert file")
            
            span.set_attribute("file.id", id)
            return id
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def update_file(id: str, file: UpdateFile):
    with tracer.start_as_current_span("update_file") as span:
        try:
            span.set_attributes({
                "id": id,
                "status": file.status,
                "table": "otel-observability-files"
            })

            db = boto3.client('dynamodb', region_name=AWS_REGION)
            res = db.update_item(
                TableName='otel-observability-files',
                Key={'id': {'S': id}},
                # #st is a placeholder for status because status is a reserved word
                UpdateExpression='set #st = :status',
                ExpressionAttributeNames={'#st': 'status'},
                ExpressionAttributeValues={':status': {'S': file.status}},
            )
            if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                raise Exception("Failed to update file")

        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise e


def delete_file(id: str):
    db = boto3.client('dynamodb', region_name=AWS_REGION)
    return db.delete_item(
        TableName='otel-observability-files',
        Key={'id': {'S': id}},
    )
