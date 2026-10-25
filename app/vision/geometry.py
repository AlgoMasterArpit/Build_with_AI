from __future__ import annotations

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray

Quad = list[list[int]]
Image = MatLike


def order_quad(points: NDArray[np.float32]) -> NDArray[np.float32]:
    pts = points.reshape(4, 2).astype(np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).ravel()
    return np.array(
        [pts[sums.argmin()], pts[diffs.argmin()], pts[sums.argmax()], pts[diffs.argmax()]],
        dtype=np.float32,
    )


def straighten(image: Image, quad: Quad, pad: float = 0.08) -> Image:
    tl, tr, br, bl = order_quad(np.array(quad, dtype=np.float32))
    width = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    height = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    width, height = max(width, 1), max(height, 1)
    dx, dy = width * pad, height * pad
    src = np.array([tl, tr, br, bl], dtype=np.float32)
    dst = np.array(
        [[dx, dy], [width + dx, dy], [width + dx, height + dy], [dx, height + dy]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    size = (int(width + 2 * dx), int(height + 2 * dy))
    return cv2.warpPerspective(
        image, matrix, size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def quad_height(quad: Quad) -> float:
    tl, tr, br, bl = order_quad(np.array(quad, dtype=np.float32))
    return float((np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2)


def quad_bounds(quad: Quad) -> tuple[int, int, int, int]:
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    return min(xs), min(ys), max(xs), max(ys)


def scale_quad(quad: object, sx: float, sy: float) -> Quad:
    return [[round(float(x) * sx), round(float(y) * sy)] for x, y in np.asarray(quad).reshape(4, 2)]
