from opentelemetry import trace

from .services import (
    update_file_status, copy_content_to_redshift, 
    get_file_metadata
)
from .instrumentation import setup_instrumentation

setup_instrumentation()

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("main") 
def main(event, context):
    span = trace.get_current_span()
    span.set_attribute("event", event)

    for r in event["Records"]:
        process_message(r)


@tracer.start_as_current_span("process_message")
def process_message(msg):
    span = trace.get_current_span()
    # create a link with the message producer
    trace_id = msg["messageAttributes"]["trace_id"]["stringValue"]
    span_id = msg["messageAttributes"]["span_id"]["stringValue"]
    span.add_link(trace.SpanContext(
        trace_id=int(trace_id), span_id=int(span_id), is_remote=True, 
        trace_flags=trace.TraceFlags.SAMPLED, trace_state=trace.TraceState() 
    ))

    file_id = msg["messageAttributes"]["file_id"]["stringValue"]
    file_name = msg["messageAttributes"]["file_name"]["stringValue"]

    span.set_attributes({"file.id": file_id, "file.name": file_name})

    print("file_id:", file_id, "file name:", file_name)

    update_file_status(file_id, "loading")

    file = get_file_metadata(file_id)
    copy_content_to_redshift(file)

    update_file_status(file_id, "loaded")
