import { trace, SpanStatusCode, context } from "@opentelemetry/api"

const tracer = trace.getTracer("frontend")


export async function fetchWithSpan(spanName, url, options) {
  const span = tracer.startSpan(spanName)

  return context.with(trace.setSpan(context.active(), span), async () => {
    try {
      const res = await fetch(url, options);
      if (!res.ok) {
        throw new Error(await res.text())
      }

      span.end()
      return res

    } catch (error) {
      span.setStatus(SpanStatusCode.ERROR)
      span.setAttribute("error", true)
      span.recordException(error)
      span.end()
      throw error
    }
  })
}