from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.config import Settings
from app.main import create_app
from app.store.photos import PhotoStore
from app.store.seeding import seed_hostel
from app.store.table import Table
from app.vision.ocr import DETECTOR_FILE, RECOGNIZER_FILE

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-round-token"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None, aws_endpoint_url=None, llm_provider="none", models_dir=ROOT / "models"
    )


@pytest.fixture
def hostel() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((ROOT / "seed" / "hostel_a.json").read_text("utf-8"))
    return data


@pytest.fixture
def aws() -> Iterator[None]:
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield


@pytest.fixture
def table(aws: None, settings: Settings, hostel: dict[str, Any]) -> Table:
    table = Table(settings)
    table.create_if_missing()
    PhotoStore(settings).create_if_missing()
    seed_hostel(table, hostel, token=TOKEN)
    return table


@pytest.fixture
def client(table: Table, settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings), headers={"x-round-token": TOKEN}) as c:
        yield c


@pytest.fixture
def models_ready() -> None:
    if not all((ROOT / "models" / name).exists() for name in (DETECTOR_FILE, RECOGNIZER_FILE)):
        pytest.skip("models missing: run `uv run python scripts/fetch_models.py`")
