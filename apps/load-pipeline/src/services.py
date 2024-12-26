import os

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REDSHIFT_WORKGROUP = os.getenv("REDSHIFT_WORKGROUP")
REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE")


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


def copy_content_to_redshift(file_name: str):
    redshift = boto3.client('redshift-data', region_name=AWS_REGION)

    create_table_command = f"""
        CREATE TABLE IF NOT EXISTS files_data (
            id VARCHAR(255),
            file_name VARCHAR(255),
            status VARCHAR(255),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
    """

    create_table_response = redshift.execute_statement(
        WorkgroupName=REDSHIFT_WORKGROUP,
        Database=REDSHIFT_DATABASE,
        Sql=create_table_command
    )

    if create_table_response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to create table")

    copy_command = f"""
        COPY files_data 
        FROM 's3://{S3_BUCKET_NAME}/{file_name}'
        IAM_ROLE default
        REGION '{AWS_REGION}'
        IGNOREHEADER 1
        FORMAT CSV;
    """

    response = redshift.execute_statement(
        WorkgroupName=REDSHIFT_WORKGROUP,
        Database=REDSHIFT_DATABASE,
        Sql=copy_command
    )

    if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception("Failed to copy file to Redshift")

    return response['Id']
