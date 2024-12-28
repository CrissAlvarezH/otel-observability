import os
import time
import re

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REDSHIFT_WORKGROUP = os.getenv("REDSHIFT_WORKGROUP")
REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE")


def get_file_metadata(file_id: str):
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


def copy_content_to_redshift(file: dict):
    redshift = boto3.client('redshift-data', region_name=AWS_REGION)

    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', file["filename"])

    print("creating table", table_name, "for file", file["filename"])
    exec_and_wait(redshift, f"""
        CREATE TABLE IF NOT EXISTS "public"."{table_name}" (
            {', '.join([f'"{c}" VARCHAR(10000)' for c in file["columns"]])}
        );
    """)

    print("copying data from s3 to redshift to table:", table_name,"file:", file["filename"])
    exec_and_wait(redshift, f"""
        COPY {table_name}
        FROM 's3://{S3_BUCKET_NAME}/{file['filename']}'
        IAM_ROLE default
        REGION '{AWS_REGION}'
        IGNOREHEADER 1
        FORMAT CSV;
    """, max_checks=-1)


def exec_and_wait(client: boto3.client, query: str, max_checks: int = 20):
    """
        Executes a query and waits for it to finish.
        If max_checks is not provided, it will wait indefinitely.

        Parameters:
            client: boto3 client of redshift
            query: query to execute
            max_checks: maximum number of checks to wait for the query to finish (-1 for infinite)
    """
    stm = client.execute_statement(
        WorkgroupName=REDSHIFT_WORKGROUP,
        Database=REDSHIFT_DATABASE,
        Sql=query
    )
    if stm.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to execute statement")

    query_id = stm.get('Id')

    last_status = ""
    status = ""
    checks = 0
    while status != 'FINISHED':
        desc = client.describe_statement(Id=query_id)
        status = desc.get('Status')

        # show logs only if status changed
        if last_status != status:
            print("describe statement:", status, desc, "... waiting 5 seconds")
            last_status = status

        if status == 'FAILED':
            raise Exception("Failed to copy data")

        if max_checks  > -1:
            checks += 1
            if checks > max_checks:
                raise Exception("Timeout waiting for copy data to finish")
        time.sleep(5)

    return query_id
