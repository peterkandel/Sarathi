from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from .config import LoggingSettings

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_context: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_context.get()
        correlation_id = correlation_id_context.get()
        if request_id:
            payload["request_id"] = request_id
        if correlation_id:
            payload["correlation_id"] = correlation_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: LoggingSettings, *, service_name: str | None = None) -> None:
    handler: logging.Handler = logging.StreamHandler()
    if settings.json:
        handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.level.upper())
    root_logger.addHandler(handler)

    if service_name:
        logging.getLogger(service_name).setLevel(settings.level.upper())


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)


def set_request_context(*, request_id: str | None = None, correlation_id: str | None = None) -> None:
    request_id_context.set(request_id)
    correlation_id_context.set(correlation_id)
