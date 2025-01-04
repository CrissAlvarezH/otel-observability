import { trace, SpanStatusCode, context, propagation } from "@opentelemetry/api"

const tracer = trace.getTracer("frontend")


export async function fetchWithSpan(spanName, url, options) {
  const span = tracer.startSpan(spanName)
  const ctx = trace.setSpan(context.active(), span)

  return context.with(ctx, async () => {
    try {
      const headers = options.headers || {}
      // propagation.inject(ctx, headers)

      const res = await fetch(url, { ...options, headers });
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