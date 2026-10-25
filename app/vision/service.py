"""Standalone vision API, so the OpenCV work can run on a separate host (e.g. Graviton + COOL).

uvicorn app.vision.service:app --host 0.0.0.0 --port 8100
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Annotated, Any

import cv2
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.vision.pipeline import MeterReader, decode_image, text_read_from_dict
from app.vision.reread import VARIANTS

app = FastAPI(title="MeterMind vision")
reader = MeterReader(get_settings().models_dir)


async def _image(photo: UploadFile) -> Any:
    image = decode_image(await photo.read())
    if image is None:
        raise HTTPException(422, "not a usable image")
    return image


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "opencv": cv2.__version__}


@app.post("/analyze")
async def analyze(
    photo: Annotated[UploadFile, File()], expected_serial: Annotated[str, Form()] = ""
) -> dict[str, Any]:
    return reader.analyze(await _image(photo), expected_serial or None).to_dict()


@app.post("/reread")
async def reread(
    photo: Annotated[UploadFile, File()],
    display: Annotated[str, Form()],
    variant: Annotated[str, Form()],
) -> dict[str, Any]:
    current = text_read_from_dict(json.loads(display))
    if current is None or variant not in VARIANTS:
        raise HTTPException(422, "bad display or variant")
    return asdict(reader.reread(await _image(photo), current, variant))
