import boto3
from datetime import datetime
from ulid import ULID

from pydantic import BaseModel, Field
from boto3.dynamodb.conditions import Key

from config import AWS_REGION

class InsertFile(BaseModel):
    filename: str
    file_size: int
    status: str = Field(default='pending', description='pending, stored, loaded')


class UpdateFile(BaseModel):
    status: str = Field(default='pending', description='pending, stored, loaded')


class File(BaseModel):
    id: str
    creation_datetime: str
    filename: str
    file_size: int
    status: str = Field(default='pending', description='pending, stored, loaded')


def get_files(page_size: int = 10, last_id: str = None):
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
    
    return {
        'items': rs.get('Items', []),
        'last_id': rs.get('LastEvaluatedKey', {}).get('id'),
        'has_more': 'LastEvaluatedKey' in rs
    }


def insert_file(file: InsertFile) -> str:
    db = boto3.client('dynamodb', region_name=AWS_REGION)
    id = str(ULID())
    res = db.put_item(
        TableName='otel-observability-files',
        Item={
            "id": {"S": id},
            "filename": {"S": file.filename},
            "file_size": {"N": str(file.file_size)},
            "status": {"S": file.status},
            # data_type is an artificial attribute to "hack" dynamodb 
            # because its required add a hash key in GlobalSecondaryIndexes
            "data_type": {"S": "FILE"}, 
            "creation_datetime": {"S": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        }
    )
    if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to insert file")
    return id


def update_file(id: str, file: UpdateFile):
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


def delete_file(id: str):
    db = boto3.client('dynamodb', region_name=AWS_REGION)
    return db.delete_item(
        TableName='otel-observability-files',
        Key={'id': {'S': id}},
    )
