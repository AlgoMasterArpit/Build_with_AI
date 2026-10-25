from __future__ import annotations

import cv2
import numpy as np

from app.vision.geometry import Image

FONT = cv2.FONT_HERSHEY_SIMPLEX


def digit_cell(ch: str, height: int = 120, width: int = 80) -> Image:
    cell = np.full((height, width), 235, np.uint8)
    scale = height / 40
    (tw, th), _ = cv2.getTextSize(ch, FONT, scale, 6)
    cv2.putText(cell, ch, ((width - tw) // 2, (height + th) // 2), FONT, scale, 20, 6)
    return cell


def rolling_digit(upper: str, lower: str, height: int = 120, width: int = 80) -> Image:
    strip = np.vstack([digit_cell(upper, height, width), digit_cell(lower, height, width)])
    start = height // 2
    return strip[start : start + height]


def display_strip(cells: list[Image]) -> Image:
    gap = np.full((cells[0].shape[0], 12), 235, np.uint8)
    parts: list[Image] = []
    for cell in cells:
        parts += [cell, gap]
    return np.hstack(parts[:-1])


def meter_photo(
    reading: str = "01910", serial: str = "SN 48217", half: int | None = None, rng_seed: int = 7
) -> Image:
    rng = np.random.default_rng(rng_seed)
    photo = rng.integers(70, 110, (1200, 1600, 3), dtype=np.uint8)
    photo = cv2.GaussianBlur(photo, (5, 5), 0)
    cv2.rectangle(photo, (300, 250), (1300, 950), (210, 210, 205), -1)

    cells = [digit_cell(c) for c in reading]
    if half is not None:
        upper = reading[half]
        cells[half] = rolling_digit(upper, str((int(upper) + 1) % 10))
    strip = cv2.cvtColor(display_strip(cells), cv2.COLOR_GRAY2BGR)
    h, w = strip.shape[:2]
    photo[420 : 420 + h, 500 : 500 + w] = strip

    cv2.rectangle(photo, (480, 700), (1100, 820), (238, 238, 236), -1)
    cv2.putText(photo, serial, (510, 785), FONT, 2.0, (25, 25, 25), 5)
    return photo


def with_glare(photo: Image, cell: tuple[int, int] = (0, 2)) -> Image:
    out = photo.copy()
    h, w = out.shape[:2]
    cy, cx = cell[0] * h // 3 + h // 6, cell[1] * w // 3 + w // 6
    cv2.circle(out, (cx, cy), min(h, w) // 9, (255, 255, 255), -1)
    return out


def blurred(photo: Image) -> Image:
    return cv2.GaussianBlur(photo, (0, 0), 9)


def darkened(photo: Image) -> Image:
    return (photo * 0.15).astype(np.uint8)
