from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.vision.geometry import Image

ANALYSIS_WIDTH = 1000
BLUR_MIN_SHARPNESS = 150.0
DARK_MAX_BRIGHTNESS = 60.0
GLARE_VALUE = 250
GLARE_MAX_SATURATION = 40
GLARE_MIN_CELL_SHARE = 0.03
GLARE_MIN_BLOB_SHARE = 0.002

ROWS = ("top", "middle", "bottom")
COLS = ("left", "center", "right")


@dataclass(frozen=True)
class QualityReport:
    sharpness: float
    brightness: float
    glare_cells: list[str] = field(default_factory=list)
    glare_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def _resize(image: Image) -> tuple[Image, float]:
    scale = ANALYSIS_WIDTH / image.shape[1]
    if scale >= 1:
        return image, 1.0
    small = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return small, scale


def _sharpness(gray: Image, grid: int = 4) -> float:
    # Meter faces have large flat areas, so score the most detailed tile, not the whole frame.
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    h, w = laplacian.shape
    tiles = [
        laplacian[r * h // grid : (r + 1) * h // grid, c * w // grid : (c + 1) * w // grid].var()
        for r in range(grid)
        for c in range(grid)
    ]
    return float(max(tiles))


def _glare_mask(hsv: Image) -> Image:
    value, saturation = hsv[..., 2], hsv[..., 1]
    mask = ((value >= GLARE_VALUE) & (saturation <= GLARE_MAX_SATURATION)).astype(np.uint8) * 255
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def _glare_cells(mask: Image) -> list[str]:
    h, w = mask.shape
    cells = []
    for r, row in enumerate(ROWS):
        for c, col in enumerate(COLS):
            cell = mask[r * h // 3 : (r + 1) * h // 3, c * w // 3 : (c + 1) * w // 3]
            if cell.size and np.count_nonzero(cell) / cell.size >= GLARE_MIN_CELL_SHARE:
                cells.append(f"{row}-{col}")
    return cells


def _glare_boxes(mask: Image, scale: float) -> list[tuple[int, int, int, int]]:
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    min_area = GLARE_MIN_BLOB_SHARE * mask.size
    boxes = []
    for x, y, w, h, area in stats[1:count]:
        if area >= min_area:
            boxes.append(
                (round(x / scale), round(y / scale), round((x + w) / scale), round((y + h) / scale))
            )
    return boxes


def assess(image: Image) -> QualityReport:
    small, scale = _resize(image)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    sharpness = _sharpness(gray)
    brightness = float(hsv[..., 2].mean())
    mask = _glare_mask(hsv)
    cells = _glare_cells(mask)

    issues = []
    if brightness < DARK_MAX_BRIGHTNESS:
        issues.append("dark")
    elif sharpness < BLUR_MIN_SHARPNESS:
        issues.append("blur")
    if cells:
        issues.append("glare")

    return QualityReport(
        sharpness=round(sharpness, 1),
        brightness=round(brightness, 1),
        glare_cells=cells,
        glare_boxes=_glare_boxes(mask, scale) if cells else [],
        issues=issues,
    )
