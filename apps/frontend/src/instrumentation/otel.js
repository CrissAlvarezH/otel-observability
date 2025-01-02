import { WebTracerProvider } from "@opentelemetry/sdk-trace-web"
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base"
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http"
import { Resource } from "@opentelemetry/resources"
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions"
import { registerInstrumentations } from "@opentelemetry/instrumentation"
import { getWebAutoInstrumentations } from "@opentelemetry/auto-instrumentations-web" 

import { OTLP_EXPORTER_URL } from "./../lib/config"


const exporter = new OTLPTraceExporter({ url: OTLP_EXPORTER_URL })

const provider = new WebTracerProvider({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: "frontend"
  }),
  spanProcessors: [
    new BatchSpanProcessor(exporter)
  ]
})
provider.register()

registerInstrumentations({
  instrumentations: [getWebAutoInstrumentations()]
})

