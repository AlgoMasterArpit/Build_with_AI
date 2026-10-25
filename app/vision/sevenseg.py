from __future__ import annotations

import cv2
import numpy as np

from app.vision.geometry import Image
from app.vision.ocr import Recognition

# Segment order: top, top-right, bottom-right, bottom, bottom-left, top-left, middle.
PATTERNS = {
    (1, 1, 1, 1, 1, 1, 0): "0",
    (0, 1, 1, 0, 0, 0, 0): "1",
    (1, 1, 0, 1, 1, 0, 1): "2",
    (1, 1, 1, 1, 0, 0, 1): "3",
    (0, 1, 1, 0, 0, 1, 1): "4",
    (1, 0, 1, 1, 0, 1, 1): "5",
    (1, 0, 1, 1, 1, 1, 1): "6",
    (1, 1, 1, 0, 0, 0, 0): "7",
    (1, 1, 1, 0, 0, 1, 0): "7",
    (1, 1, 1, 1, 1, 1, 1): "8",
    (1, 1, 1, 1, 0, 1, 1): "9",
    (1, 1, 1, 0, 0, 1, 1): "9",
}

SEGMENT_BOXES = (
    (0.2, 0.0, 0.8, 0.15),
    (0.75, 0.1, 1.0, 0.45),
    (0.75, 0.55, 1.0, 0.9),
    (0.2, 0.85, 0.8, 1.0),
    (0.0, 0.55, 0.25, 0.9),
    (0.0, 0.1, 0.25, 0.45),
    (0.2, 0.42, 0.8, 0.58),
)


def _foreground(gray: Image) -> Image:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.count_nonzero(binary) > binary.size / 2:
        binary = cv2.bitwise_not(binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, max(3, gray.shape[0] // 20)))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


def _digit_boxes(mask: Image) -> list[tuple[int, int, int, int]]:
    h = mask.shape[0]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(c) for c in contours]
    boxes = [(x, y, w, bh) for x, y, w, bh in rects if bh >= 0.45 * h]
    if not boxes:
        return []
    typical = int(np.median([w for _, _, w, bh in boxes if w > 0.3 * bh] or [b[2] for b in boxes]))
    widened = []
    for x, y, w, bh in sorted(boxes):
        if w < 0.5 * typical:
            x, w = x + w - typical, typical
        widened.append((max(0, x), y, w, bh))
    return widened


def _read_digit(mask: Image, box: tuple[int, int, int, int]) -> tuple[str, float] | None:
    x, y, w, h = box
    cell = mask[y : y + h, x : x + w]
    states, margins = [], []
    for x0, y0, x1, y1 in SEGMENT_BOXES:
        region = cell[
            int(y0 * h) : max(int(y1 * h), int(y0 * h) + 1),
            int(x0 * w) : max(int(x1 * w), int(x0 * w) + 1),
        ]
        fill = np.count_nonzero(region) / max(region.size, 1)
        states.append(int(fill > 0.4))
        margins.append(min(1.0, abs(fill - 0.4) / 0.4))
    digit = PATTERNS.get(tuple(states))  # type: ignore[arg-type]
    return (digit, float(np.mean(margins))) if digit else None


def decode(crop: Image) -> Recognition | None:
    gray = crop if crop.ndim == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    mask = _foreground(gray)
    boxes = _digit_boxes(mask)
    reads = [_read_digit(mask, b) for b in boxes]
    if not reads or any(r is None for r in reads):
        return None
    return Recognition("".join(r[0] for r in reads if r), [round(r[1], 3) for r in reads if r])
