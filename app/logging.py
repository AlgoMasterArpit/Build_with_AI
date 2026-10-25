from __future__ import annotations

import json
import logging
import sys
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

request_id: ContextVar[str] = ContextVar("request_id", default="-")

RESERVED = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id.get(),
            "message": record.getMessage(),
        }
        entry.update({k: v for k, v in vars(record).items() if k not in RESERVED})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    logging.getLogger("uvicorn.access").handlers[:] = []


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    token = request_id.set(request.headers.get("x-request-id") or uuid.uuid4().hex[:12])
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id.get()
        return response
    finally:
        request_id.reset(token)
