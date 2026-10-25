from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("metermind.api")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


INVALID_LINK = ApiError(404, "invalid_link", "Ye link sahi nahi hai, admin se naya link maango.")
UNKNOWN_ROOM = ApiError(404, "unknown_room", "Ye room is hostel mein nahi hai.")


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            {"error": error.code, "message": error.message}, status_code=error.status
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, error: Exception) -> JSONResponse:
        log.exception("unhandled error", extra={"error_type": type(error).__name__})
        return JSONResponse(
            {"error": "server_error", "message": "Kuch gadbad hui, dobara try karo."},
            status_code=500,
        )
