from __future__ import annotations

from pathlib import Path

import pytest

from app.vision.ocr import DETECTOR_FILE, RECOGNIZER_FILE
from app.vision.pipeline import MeterReader

MODELS = Path(__file__).resolve().parents[2] / "models"


@pytest.fixture(scope="session")
def reader() -> MeterReader:
    if not all((MODELS / name).exists() for name in (DETECTOR_FILE, RECOGNIZER_FILE)):
        pytest.skip("models missing: run `uv run python scripts/fetch_models.py`")
    return MeterReader(MODELS)
