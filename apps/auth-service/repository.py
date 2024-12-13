import boto3

from config import AWS_REGION


AUTH_TABLE = 'otel-observability-auth'


def add_token(username: str, token: str):
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    return table.put_item(Item={
        'username': username,
        'token': token,
    })


def scan_tokens():
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    return table.scan()['Items']


def get_token(username: str):
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    return table.get_item(Key={
        'username': username,
    })
