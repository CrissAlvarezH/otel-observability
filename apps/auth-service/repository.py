import boto3
import uuid
from faker import Faker

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


def get_token(token: str):
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    res = table.get_item(Key={'token': token})
    return res.get('Item', None)


def seed_tokens():
    tokens = scan_tokens()
    if len(tokens) > 0:
        return

    faker = Faker()
    for _ in range(4):
        add_token(faker.user_name(), uuid.uuid4().hex[:20])
