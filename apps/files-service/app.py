from typing import List

from fastapi import FastAPI, Body, Query, Path, Depends, Request, Response
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace

from repositories.files import (
    get_files, update_file, insert_file, InsertFile, UpdateFile,
    delete_file,
)
from dependencies import get_username, auth
from services.aws import (
    init_upload, FilePart, complete_upload, get_presigned_url,
    list_multipart_uploads, queue_uploaded_file,
)
from instrumentation import setup_tracing
setup_tracing()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["traceparent", "tracestate"]
)

FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)


@app.post("/upload/init")
def init_upload_route(
    filename: str = Body(),
    file_size: int = Body(),
    columns: List[str] = Body(),
    row_count: int = Body(),
    username: str = Depends(get_username),
):
    span = trace.get_current_span()
    span.set_attributes({
        "file.name": filename, "file.size": file_size,
        "file.rows": row_count, "file.columns": columns
    })

    upload_id = init_upload(filename)

    file_id = insert_file(InsertFile(
        filename=filename,
        file_size=file_size,
        username=username,
        columns=columns,
        row_count=row_count,
    ))

    return {"upload_id": upload_id, "file_id": file_id}


@app.post("/upload/get-presigned-url", dependencies=[Depends(auth)])
def get_presigned_url_route(
    filename: str = Body(),
    upload_id: str = Body(),
    part_number: int = Body(),
):
    span = trace.get_current_span()
    span.set_attributes({
        "upload.id": upload_id, "part.number": part_number,
        "file.name": filename
    })

    presigned_url = get_presigned_url(filename, upload_id, part_number)

    return {"url": presigned_url}


@app.post("/upload/complete", dependencies=[Depends(auth)])
def complete_upload_route(
    file_id: str = Body(),
    filename: str = Body(),
    upload_id: str = Body(),
    parts: List[FilePart] = Body(),
):
    span = trace.get_current_span()
    span.set_attributes({
        "file.id": file_id, "file.name": filename,
        "upload.id": upload_id, "parts.count": len(parts)
    })
    try:
        complete_upload(filename, upload_id, parts)
    except Exception as e:
        print(e)
        span.set_status(trace.StatusCode.ERROR)
        span.set_attribute("error", str(e))

        update_file(file_id, UpdateFile( status="failed"))
        return {"message": "Upload failed"}

    update_file(file_id, UpdateFile(status="stored"))

    queue_uploaded_file(file_id, filename)

    return {"message": "Upload completed"}


@app.get("/upload/list-multipart-uploads")
def list_multipart_uploads_route():
    return list_multipart_uploads()


@app.get("/files")
def get_files_route(
    page_size: int = Query(default=10),
    last_id: str = Query(default=None),
):
    res = get_files(page_size, last_id)

    if not res["has_more"]:
        return {"result": res["items"]}

    return {
        "pagination": {
            "last_id": res["last_id"],
            "has_more": res["has_more"],
        },
        "result": res["items"],
    }


@app.post("/files")
def insert_file_route(file: InsertFile):
    return insert_file(file)


@app.put("/files/{id}")
def update_file_route(file: UpdateFile, id: str = Path()):
    return update_file(id, file)


@app.delete("/files/{id}")
def delete_file_route(id: str = Path()):
    return delete_file(id)
