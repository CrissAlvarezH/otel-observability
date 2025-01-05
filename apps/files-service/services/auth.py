from typing import Tuple
import requests
from opentelemetry.propagate import inject
from opentelemetry import trace

from config import AUTH_DOMAIN

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("validate_token", kind=trace.SpanKind.CLIENT)
def validate_token(token: str) -> Tuple[bool, dict]:
    headers = {}
    inject(headers)

    res = requests.post(
        f"{AUTH_DOMAIN}/validate",
        json={"token": token},
        headers=headers
    )
    if res.status_code != 200:
        return False, None

    return True, res.json()