import os
import time
import re

import boto3
from opentelemetry import trace

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REDSHIFT_WORKGROUP = os.getenv("REDSHIFT_WORKGROUP")
REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE")

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("get_file_metadata")
def get_file_metadata(file_id: str):
    span = trace.get_current_span()
    span.set_attributes({"file.id": file_id, "table.name": "otel-observability-files"})

    db = boto3.client('dynamodb', region_name=AWS_REGION)
    res = db.get_item(
        TableName='otel-observability-files',
        Key={'id': {'S': file_id}},
    )
    if res.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to get file metadata")

    item = res.get('Item', None)
    if not item:
        raise Exception("File not found")

    # transform dynamodb format to a dict
    data = {}
    for k, v in item.items():
        if "L" in v:
            data[k] = [c['S'] for c in v['L']]
        else:
            data[k] = v['S'] if "S" in v else v['N']

    return data


@tracer.start_as_current_span("update_file_status") 
def update_file_status(file_id: str, status: str):
    span = trace.get_current_span()
    span.set_attributes({
        "file.id": file_id, "file.status": status, 
        "table.name": "otel-observability-files"
    })

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


@tracer.start_as_current_span("copy_content_to_redshift") 
def copy_content_to_redshift(file: dict):
    span = trace.get_current_span()
    span.set_attributes({
        "file.name": file["filename"], "file.id": file["id"], 
        "file.columns": file["columns"], "bucket.name": S3_BUCKET_NAME
    })

    redshift = boto3.client('redshift-data', region_name=AWS_REGION)

    # remove file extension from filename
    filename = os.path.splitext(file["filename"])[0]
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', filename)

    span.set_attribute("wharehouse.table.name", table_name)

    print("creating table", table_name, "for file", file["filename"])
    exec_and_wait(redshift, f"""
        CREATE TABLE IF NOT EXISTS "public"."{table_name}" (
            "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "file_id" VARCHAR(10000) DEFAULT '{file["id"]}',
            "file_name" VARCHAR(10000) DEFAULT '{file["filename"]}',
            {', '.join([f'"{c}" VARCHAR(10000)' for c in file["columns"]])}
        );
    """)

    print("copying data from s3 to redshift to table:", table_name,"file:", file["filename"])
    exec_and_wait(redshift, f"""
        COPY {table_name} ({', '.join([f'"{c}"' for c in file["columns"]])})
        FROM 's3://{S3_BUCKET_NAME}/{file['filename']}'
        IAM_ROLE default
        REGION '{AWS_REGION}'
        IGNOREHEADER 1
        FORMAT CSV;
    """, max_checks=-1)


@tracer.start_as_current_span("exec_and_wait_query") 
def exec_and_wait(client: boto3.client, query: str, max_checks: int = 20):
    """
        Executes a query and waits for it to finish.
        If max_checks is not provided, it will wait indefinitely.

        Parameters:
            client: boto3 client of redshift
            query: query to execute
            max_checks: maximum number of checks to wait for the query to finish (-1 for infinite)
    """
    exec_span = trace.get_current_span()
    exec_span.set_attribute("warehouse.query", query)

    stm = client.execute_statement(
        WorkgroupName=REDSHIFT_WORKGROUP,
        Database=REDSHIFT_DATABASE,
        Sql=query
    )
    if stm.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to execute statement")

    query_id = stm.get('Id')

    exec_span.set_attribute("query.id", query_id)

    last_status = ""
    checks = 0
    while True:
        with tracer.start_as_current_span("check-query-status") as check_span:
            if max_checks  > -1:
                checks += 1
                if checks > max_checks:
                    check_span.add_event("max-checks")
                    raise Exception("Timeout waiting for copy data to finish")

            desc = client.describe_statement(Id=query_id)
            status = desc.get('Status')

            check_span.set_attribute("warehouse.query.status", status)

            # show logs only if status changed
            if last_status != status:
                print("describe statement:", status, desc, "... waiting 1 second")
                last_status = status

            if status == 'FINISHED':
                check_span.add_event("warehouse.query.finished")
                break

            if status == 'FAILED':
                check_span.add_event("warehouse.query.failed")
                check_span.set_attribute("error", True)
                raise Exception("Failed to copy data")

            time.sleep(1)

    return query_id
