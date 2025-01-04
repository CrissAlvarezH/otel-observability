import uuid

from faker import Faker
import boto3
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from config import AWS_REGION


AUTH_TABLE = 'otel-observability-auth'

tracer = trace.get_tracer("auth-service")


def add_token(username: str, token: str):
    with tracer.start_as_current_span("add_token") as span:
        try:
            span.set_attribute("user.username", username)
            span.set_attribute("db.table", AUTH_TABLE)

            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(AUTH_TABLE)
            return table.put_item(Item={
                'username': username,
                'token': token,
            })
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise e


def scan_tokens():
    with tracer.start_as_current_span("scan_tokens") as span:
        try:
            span.set_attribute("db.table", AUTH_TABLE)

            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(AUTH_TABLE)
            return table.scan()['Items']
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            raise e


def get_token(token: str):
    with tracer.start_as_current_span("get_token") as span:
        try:
            span.set_attribute("db.table", AUTH_TABLE)

            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(AUTH_TABLE)
            res = table.get_item(Key={'token': token})
            return res.get('Item', None)
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)


def seed_tokens():
    with tracer.start_as_current_span("seed_token") as span:
        try:
            span.set_attribute("db.table", AUTH_TABLE)

            tokens = scan_tokens()
            if len(tokens) > 0:
                return

            faker = Faker()
            for _ in range(4):
                add_token(faker.user_name(), uuid.uuid4().hex[:20])
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
