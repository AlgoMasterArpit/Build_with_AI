from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import logging as app_logging
from app.api import errors, rounds
from app.config import Settings, get_settings
from app.store.table import Table

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app_logging.configure()

    app = FastAPI(title="MeterMind", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings
    app.state.table = Table(settings)

    app.middleware("http")(app_logging.request_id_middleware)
    errors.install(app)
    app.include_router(rounds.router)

    @app.get("/healthz", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/r/{token}", include_in_schema=False)
    def round_page(token: str) -> FileResponse:
        return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-store"})

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app


app = create_app()
