from .services import update_file_status, copy_content_to_redshift


def main(event, context):
    for r in event['Records']:
        process_message(r)


def process_message(msg):
    file_id = msg["messageAttributes"]["file_id"]["stringValue"]
    file_name = msg["messageAttributes"]["file_name"]["stringValue"]

    print("file_id:", file_id, "file name:", file_name)

    update_file_status(file_id, "loading")

    copy_content_to_redshift(file_name)

    update_file_status(file_id, "loaded")
