from __future__ import annotations

from collections.abc import Callable

import cv2

from app.vision.geometry import Image


def _gray(crop: Image) -> Image:
    return crop if crop.ndim == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)


def clahe(crop: Image) -> Image:
    return cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(_gray(crop))


def threshold(crop: Image) -> Image:
    gray = cv2.GaussianBlur(_gray(crop), (3, 3), 0)
    block = max(15, (min(gray.shape[:2]) // 4) | 1)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, 10
    )


def invert(crop: Image) -> Image:
    return cv2.bitwise_not(_gray(crop))


def upscale(crop: Image) -> Image:
    big = cv2.resize(_gray(crop), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blurred = cv2.GaussianBlur(big, (0, 0), 2)
    return cv2.addWeighted(big, 1.6, blurred, -0.6, 0)


VARIANTS: dict[str, Callable[[Image], Image]] = {
    "clahe": clahe,
    "threshold": threshold,
    "invert": invert,
    "upscale": upscale,
}


def apply(variant: str, crop: Image) -> Image:
    return VARIANTS[variant](crop)
