import os 

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.semconv.resource import ResourceAttributes

OTLP_SPAN_EXPORTER_ENDPOINT = os.getenv("OTLP_SPAN_EXPORTER_ENDPOINT")


def setup_instrumentation():
    BotocoreInstrumentor().instrument()

    exporter = OTLPSpanExporter(endpoint=OTLP_SPAN_EXPORTER_ENDPOINT)
    processor = BatchSpanProcessor(exporter)

    resource = Resource.create({ResourceAttributes.SERVICE_NAME: "load-pipeline"})
    provider = TracerProvider(resource=resource)

    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

