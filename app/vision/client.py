from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import cv2
import httpx

from app.vision.geometry import Image
from app.vision.pipeline import Analysis, MeterReader, TextRead, text_read_from_dict


class Vision(Protocol):
    def analyze(self, image: Image, expected_serial: str | None) -> Analysis: ...

    def reread(self, image: Image, display: TextRead, variant: str) -> TextRead: ...


@lru_cache(maxsize=2)
def _reader(models_dir: Path) -> MeterReader:
    return MeterReader(models_dir)


class InProcessVision:
    def __init__(self, models_dir: Path) -> None:
        self._reader = _reader(models_dir.resolve())

    def analyze(self, image: Image, expected_serial: str | None) -> Analysis:
        return self._reader.analyze(image, expected_serial)

    def reread(self, image: Image, display: TextRead, variant: str) -> TextRead:
        return self._reader.reread(image, display, variant)


class HttpVision:
    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    @staticmethod
    def _jpeg(image: Image) -> bytes:
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            raise ValueError("could not encode image")
        return encoded.tobytes()

    def analyze(self, image: Image, expected_serial: str | None) -> Analysis:
        response = self._client.post(
            "/analyze",
            files={"photo": ("photo.jpg", self._jpeg(image), "image/jpeg")},
            data={"expected_serial": expected_serial or ""},
        )
        response.raise_for_status()
        return Analysis.from_dict(response.json())

    def reread(self, image: Image, display: TextRead, variant: str) -> TextRead:
        response = self._client.post(
            "/reread",
            files={"photo": ("photo.jpg", self._jpeg(image), "image/jpeg")},
            data={"display": json.dumps(asdict(display)), "variant": variant},
        )
        response.raise_for_status()
        read = text_read_from_dict(response.json())
        if read is None:
            raise ValueError("vision service returned no display")
        return read


def build_vision(models_dir: Path, vision_url: str | None) -> Vision:
    return HttpVision(vision_url) if vision_url else InProcessVision(models_dir)
