import { WebTracerProvider } from "@opentelemetry/sdk-trace-web"
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base"
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http"
import { Resource } from "@opentelemetry/resources"
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions"
import { registerInstrumentations } from "@opentelemetry/instrumentation"
import { getWebAutoInstrumentations } from "@opentelemetry/auto-instrumentations-web" 
import { W3CTraceContextPropagator } from "@opentelemetry/core"
import { propagation } from "@opentelemetry/api"

import { OTLP_COLLECTOR_ENDPOINT } from "./../lib/config"

propagation.setGlobalPropagator(new W3CTraceContextPropagator())

const exporter = new OTLPTraceExporter({ url: OTLP_COLLECTOR_ENDPOINT })

const provider = new WebTracerProvider({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: "frontend"
  }),
  spanProcessors: [
    new BatchSpanProcessor(exporter),
    {
      onStart: (span) => {
        if (span.name == "click") {
          // change the name of the span from "click" to "click:<element-id>"
          const xpath =span.attributes["target_xpath"]
          if (xpath.includes("id=")) {
            // example: //*[@id="input-pick-file"]
            const id = xpath.split("id=")[1].split("\"")[1]
            span.updateName(`click:${id}`)
          }
        }
      },
      onEnd: () => {}
    }
  ]
})

provider.register()

registerInstrumentations({
  instrumentations: [getWebAutoInstrumentations({
    "@opentelemetry/instrumentation-fetch": {
      propagateTraceHeaderCorsUrls: /.*/,  // Propagate to all URLs
      clearTimingResources: true,
    },
  })]
})

