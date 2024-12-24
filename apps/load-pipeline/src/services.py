import os

import boto3

AWS_REGION = os.getenv("AWS_REGION")


def update_file_status(file_id: str, status: str):
    db = boto3.client('dynamodb', region_name=AWS_REGION)
    res = db.update_item(
        TableName='otel-observability-files',
        Key={'id': {'S': file_id}},
        # #st is a placeholder for status because status is a reserved word
        UpdateExpression='set #st = :status',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={':status': {'S': status}},
    )
    if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to update file")