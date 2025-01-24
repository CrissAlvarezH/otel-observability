import os 

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.semconv.resource import ResourceAttributes

OTLP_COLLECTOR_ENDPOINT = os.getenv("OTLP_COLLECTOR_ENDPOINT")


def setup_instrumentation():
    BotocoreInstrumentor().instrument()

    exporter = OTLPSpanExporter(endpoint=OTLP_COLLECTOR_ENDPOINT)
    # use simple processor to avoid batching and losing spans because of timeout of 15 minutes
    # of the execution lambda function
    processor = SimpleSpanProcessor(exporter) 

    resource = Resource.create({ResourceAttributes.SERVICE_NAME: "load-pipeline"})
    provider = TracerProvider(resource=resource)

    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

