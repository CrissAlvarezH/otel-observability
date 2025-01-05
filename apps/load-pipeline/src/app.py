from opentelemetry import trace
from opentelemetry.trace import StatusCode

from .services import (
    update_file_status, copy_content_to_redshift, 
    get_file_metadata
)
from .instrumentation import setup_instrumentation

setup_instrumentation()

tracer = trace.get_tracer(__name__)


def main(event, context):
    with tracer.start_as_current_span("main") as span:
        try:
            span.set_attribute("event", event)

            for r in event["Records"]:
                process_message(r)

        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            span.set_attribute({"error": True})
            raise e


def process_message(msg):
    with tracer.start_as_current_span("process_message") as span:
        file_id = msg["messageAttributes"]["file_id"]["stringValue"]
        file_name = msg["messageAttributes"]["file_name"]["stringValue"]

        span.set_attributes({"file.id": file_id, "file.name": file_name})

        print("file_id:", file_id, "file name:", file_name)

        update_file_status(file_id, "loading")

        file = get_file_metadata(file_id)
        copy_content_to_redshift(file)

        update_file_status(file_id, "loaded")
