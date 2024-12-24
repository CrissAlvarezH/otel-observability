from fastapi import HTTPException, Header, Depends

from services.auth import validate_token


async def auth(token: str = Header()):
    if not token:
        raise HTTPException(status_code=401)

    ok, user = validate_token(token)
    if not ok:
        raise HTTPException(status_code=401)

    return user


async def get_username(token: dict = Depends(auth)):
    return token["username"]
