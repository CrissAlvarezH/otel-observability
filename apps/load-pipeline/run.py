import os

import boto3

os.environ["AWS_REGION"] = "us-east-1"
os.environ["REDSHIFT_WORKGROUP"] = "otel-observability-workgroup"
os.environ["REDSHIFT_DATABASE"] = "otel-observability"

from src.services import exec_and_wait


if __name__ == "__main__":
    AWS_REGION = "us-east-1"

    redshift = boto3.client('redshift-data', region_name=AWS_REGION)

    sql = """
        CREATE TABLE IF NOT EXISTS "public"."local_table" (
            name TEXT,
            age INT,
            job TEXT
        );
    """
    query_id = exec_and_wait(redshift, sql)

    sql = """
        INSERT INTO "public"."local_table" (name, age, job)
        VALUES ('John', 30, 'Developer');
    """
    query_id = exec_and_wait(redshift, sql)
