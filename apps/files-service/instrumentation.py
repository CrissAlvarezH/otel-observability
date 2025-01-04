from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

from config import OTLP_SPAN_EXPORTER_ENDPOINT

def setup_tracing():
  BotocoreInstrumentor().instrument()

  resource = Resource.create({"service.name": "files-service"})

  tracer_provider = TracerProvider(resource=resource)

  otel_exporter = OTLPSpanExporter(endpoint=OTLP_SPAN_EXPORTER_ENDPOINT, insecure=True)
  span_processor = BatchSpanProcessor(otel_exporter)
  tracer_provider.add_span_processor(span_processor)

  trace.set_tracer_provider(tracer_provider)