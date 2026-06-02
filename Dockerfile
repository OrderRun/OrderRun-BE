FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10

WORKDIR /app

COPY pyproject.toml setup.py ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir --retries 10 --timeout 100 .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
