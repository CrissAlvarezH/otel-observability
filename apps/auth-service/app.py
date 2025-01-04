from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Body, Response

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from repository import add_token, scan_tokens, get_token, seed_tokens
from instrumentation import setup_tracing

setup_tracing()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

@app.post("/validate")
def validate_token(
    token: str = Body(embed=True),
):
    res = get_token(token)
    if res is not None:
        return res
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


@app.post("/seed")
def seed_tokens_route():
    seed_tokens()
    return {"message": "Tokens seeded"}
