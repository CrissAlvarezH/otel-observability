from fastapi import Request

from opentelemetry import trace
from opentelemetry.propagate import inject, extract


async def traces_midleware(req: Request, call_next):
    # get span provided for fastapi instrumentation
    span = trace.get_current_span()


    context = extract(req.headers)
    # TODO