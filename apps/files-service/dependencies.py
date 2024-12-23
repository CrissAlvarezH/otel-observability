import os
import requests
from fastapi import HTTPException, Header, Depends

AUTH_DOMAIN = os.getenv("AUTH_DOMAIN")


async def validate_token(token: str = Header()):
    if not token:
        raise HTTPException(status_code=401)
    
    res = requests.post(
        f"{AUTH_DOMAIN}/validate",
        json={"token": token}
    )
    if res.status_code != 200:
        raise HTTPException(status_code=401)
    return res.json()


async def get_username(token: dict = Depends(validate_token)):
    return token["username"]
