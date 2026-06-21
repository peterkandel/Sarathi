FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api_gateway ./apps/api_gateway
COPY packages ./packages

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" httpx pydantic-settings \
    && pip install --no-cache-dir -e /app/packages/shared_auth -e /app/packages/shared_events

CMD ["uvicorn", "apps.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
