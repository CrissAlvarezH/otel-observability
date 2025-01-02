from fastapi import HTTPException, Header, Depends
from opentelemetry import trace

from services.auth import validate_token

tracer = trace.get_tracer(__name__)

async def auth(token: str = Header()):
    with tracer.start_as_current_span("auth") as span:

        if not token:
            span.set_status(trace.StatusCode.ERROR)
            span.set_attribute("error", "token not provided")
            raise HTTPException(status_code=401)

        ok, user = validate_token(token)
        if not ok:
            span.set_status(trace.StatusCode.ERROR)
            span.set_attribute("error", "invalid token")
            raise HTTPException(status_code=401)
        
        span.set_attribute("user.username", user["username"])
    return user


async def get_username(token: dict = Depends(auth)):
    with tracer.start_as_current_span("get-username") as span:
        username = token["username"]
        span.set_attribute("user.username", username)
    return username
