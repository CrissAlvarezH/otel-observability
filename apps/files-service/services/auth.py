from typing import Tuple
import requests

from config import AUTH_DOMAIN


def validate_token(token: str) -> Tuple[bool, dict]:
    res = requests.post(
        f"{AUTH_DOMAIN}/validate",
        json={"token": token}
    )
    if res.status_code != 200:
        return False, None

    return True, res.json()

