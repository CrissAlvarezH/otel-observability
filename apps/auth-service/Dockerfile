FROM python:3.12 AS builder

WORKDIR /code

COPY ./pyproject.toml /code/pyproject.toml

RUN pip install poetry

RUN poetry export -f requirements.txt --output requirements.txt

FROM python:3.12 AS runner

WORKDIR /code

COPY --from=builder /code/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["fastapi", "run", "app.py", "--port", "80"]
