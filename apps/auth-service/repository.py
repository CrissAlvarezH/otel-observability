import uuid

from faker import Faker
import boto3
from opentelemetry import trace

from config import AWS_REGION, AUTH_TABLE


tracer = trace.get_tracer("auth-service")


@tracer.start_as_current_span("add_token") 
def add_token(username: str, token: str):
    span = trace.get_current_span()
    span.set_attribute("user.username", username)
    span.set_attribute("db.table", AUTH_TABLE)

    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    return table.put_item(Item={
        'username': username,
        'token': token,
    })


@tracer.start_as_current_span("scan_tokens") 
def scan_tokens():
    span = trace.get_current_span()
    span.set_attribute("db.table", AUTH_TABLE)

    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    return table.scan()['Items']


@tracer.start_as_current_span("get_token") 
def get_token(token: str):
    span = trace.get_current_span()
    span.set_attribute("db.table", AUTH_TABLE)

    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(AUTH_TABLE)
    res = table.get_item(Key={'token': token})
    return res.get('Item', None)


@tracer.start_as_current_span("seed_token") 
def seed_tokens():
    span = trace.get_current_span()
    span.set_attribute("db.table", AUTH_TABLE)

    tokens = scan_tokens()
    if len(tokens) > 0:
        return

    faker = Faker()
    for _ in range(4):
        add_token(faker.user_name(), uuid.uuid4().hex[:20])
