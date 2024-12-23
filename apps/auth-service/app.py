from fastapi import FastAPI, Body, Response
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from repository import add_token, scan_tokens, get_token

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate")
def validate_token(
    token: str = Body(embed=True),
):
    token = get_token(token)
    if token:
        return Response(status_code=200)
    return Response(status_code=401)


@app.post("/tokens")
def add_token_route(
    username: str = Body(),
    token: str = Body(),
):
    token = add_token(username, token)
    return {"token": token}


@app.get("/tokens")
def get_tokens_route():
    return scan_tokens()


