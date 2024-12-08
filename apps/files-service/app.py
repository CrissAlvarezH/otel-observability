from fastapi import FastAPI, Body, Query
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from services.aws import (
    init_upload, FilePart, complete_upload, get_presigned_url,
    list_multipart_uploads,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload/init")
def init_upload_route(filename: str = Body()):
    upload_id = init_upload(filename)
    return {"upload_id": upload_id}


@app.post("/upload/get-presigned-url")
def get_presigned_url_route(
    filename: str = Body(),
    upload_id: str = Body(),
    part_number: int = Body(),
):
    presigned_url = get_presigned_url(filename, upload_id, part_number)
    return {"url": presigned_url}


@app.post("/upload/complete")
def complete_upload_route(
    filename: str = Body(),
    upload_id: str = Body(),
    parts: list[FilePart] = Body(),
):
    complete_upload(filename, upload_id, parts)
    return {"message": "Upload completed"}

@app.get("/upload/list-multipart-uploads")
def list_multipart_uploads_route(filename: str = Query()):
    uploads = list_multipart_uploads(filename)
    return {"uploads": uploads}
