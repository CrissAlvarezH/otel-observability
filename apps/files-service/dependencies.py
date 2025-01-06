from fastapi import HTTPException, Header, Depends
from opentelemetry import trace

from services.auth import validate_token

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("auth")
async def auth(token: str = Header()):
    span = trace.get_current_span()

    if not token:
        raise HTTPException(status_code=401)

    ok, user = validate_token(token)
    if not ok:
        raise HTTPException(status_code=401)
    
    span.set_attribute("user.username", user["username"])
    return user


@tracer.start_as_current_span("get-username")
async def get_username(token: dict = Depends(auth)):
    span = trace.get_current_span()
    username = token["username"]
    span.set_attribute("user.username", username)
    return username
