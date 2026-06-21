FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY services ./services
COPY packages ./packages

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic-settings

CMD ["sh", "-c", "uvicorn ${SERVICE_NAME}.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
