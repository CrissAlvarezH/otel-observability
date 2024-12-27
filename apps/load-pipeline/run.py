import boto3


if __name__ == "__main__":

    client = boto3.client('redshift-data')
    res = client.list_statements(
        Status="ALL"
    )

    print("response:", res)
    for r in res.get('Statements', []):
        print("")
        print("Status:", r.get('Status'), "Id:", r.get('Id'), "Query:", r.get('QueryString'))
