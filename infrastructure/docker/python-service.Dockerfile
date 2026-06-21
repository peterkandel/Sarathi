FROM python:3.11-slim

ARG SERVICE_PATH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_PATH} /app/service
COPY packages /app/packages

RUN pip install --no-cache-dir -e /app/service \
    && pip install --no-cache-dir -e /app/packages/shared_auth -e /app/packages/shared_events

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
