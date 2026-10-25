from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from app.vision.geometry import Image, Quad, scale_quad

DETECTOR_FILE = "text_detection_en_ppocrv3_2023may.onnx"
RECOGNIZER_FILE = "text_recognition_CRNN_EN_2021sep.onnx"

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyz"
DIGITS = CHARSET[:10]
DETECT_LONG_SIDE = 1280
DB_MEAN = (122.67891434, 116.66876762, 104.00698793)


@dataclass(frozen=True)
class Recognition:
    text: str
    confidences: list[float]

    @property
    def confidence(self) -> float:
        return min(self.confidences, default=0.0)


class TextDetector:
    def __init__(self, models_dir: Path) -> None:
        self._model = cv2.dnn.TextDetectionModel_DB(
            cv2.dnn.readNet(str(models_dir / DETECTOR_FILE))
        )
        self._model.setBinaryThreshold(0.3)
        self._model.setPolygonThreshold(0.5)
        self._model.setMaxCandidates(200)
        self._model.setUnclipRatio(2.0)

    def detect(self, image: Image) -> list[Quad]:
        h, w = image.shape[:2]
        scale = DETECT_LONG_SIDE / max(h, w)
        in_w = max(32, round(w * scale / 32) * 32)
        in_h = max(32, round(h * scale / 32) * 32)
        self._model.setInputParams(1 / 255.0, (in_w, in_h), DB_MEAN, True)
        resized = cv2.resize(image, (in_w, in_h), interpolation=cv2.INTER_AREA)
        quads, _ = self._model.detect(resized)
        return [scale_quad(q, w / in_w, h / in_h) for q in quads]


class TextRecognizer:
    def __init__(self, models_dir: Path) -> None:
        self._net = cv2.dnn.readNet(str(models_dir / RECOGNIZER_FILE))

    def logits(self, crop: Image) -> NDArray[np.float32]:
        gray = crop if crop.ndim == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        blob = cv2.dnn.blobFromImage(gray, 1 / 127.5, (100, 32), 127.5)
        self._net.setInput(blob)
        out = np.asarray(self._net.forward(), dtype=np.float32)
        return out[:, 0, :]

    def read(self, crop: Image, charset: str = CHARSET) -> Recognition:
        return decode(self.logits(crop), charset)


def decode(logits: NDArray[np.float32], charset: str = CHARSET) -> Recognition:
    allowed = [0] + [CHARSET.index(c) + 1 for c in charset]
    restricted = logits[:, allowed]
    shifted = np.exp(restricted - restricted.max(axis=1, keepdims=True))
    probs = shifted / shifted.sum(axis=1, keepdims=True)
    best = probs.argmax(axis=1)

    text: list[str] = []
    confidences: list[float] = []
    run: list[float] = []
    previous = 0
    for step, index in enumerate(best):
        if index != previous and run:
            confidences.append(float(np.mean(run)))
            run = []
        if index != 0:
            if index != previous:
                text.append(charset[index - 1])
            run.append(float(probs[step, index]))
        previous = index
    if run:
        confidences.append(float(np.mean(run)))
    return Recognition("".join(text), [round(c, 3) for c in confidences])
