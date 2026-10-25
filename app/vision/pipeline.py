from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import cv2
import numpy as np

from app.vision import reread as variants
from app.vision import serials, sevenseg
from app.vision.geometry import Image, Quad, quad_height, straighten
from app.vision.ocr import DIGITS, Recognition, TextDetector, TextRecognizer, decode
from app.vision.quality import QualityReport, assess

DIGIT_CONFIDENCE_THRESHOLD = 0.85
SERIAL_MIN_CONFIDENCE = 0.6
DISPLAY_MIN_DIGITS = 4
DISPLAY_MAX_DIGITS = 9

SerialStatus = Literal["match", "mismatch", "unreadable", "read"]


@dataclass(frozen=True)
class TextRead:
    text: str
    confidences: list[float]
    quad: Quad
    height: float
    source: str = "crnn"

    @property
    def confidence(self) -> float:
        return min(self.confidences, default=0.0)

    @property
    def unclear_positions(self) -> list[int]:
        return [i for i, c in enumerate(self.confidences) if c < DIGIT_CONFIDENCE_THRESHOLD]


@dataclass(frozen=True)
class Analysis:
    width: int
    height: int
    quality: QualityReport
    display: TextRead | None
    serial: TextRead | None
    serial_status: SerialStatus
    texts: list[TextRead] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["quality"]["ok"] = self.quality.ok
        if self.display:
            data["display"]["unclear_positions"] = self.display.unclear_positions
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Analysis:
        quality = {k: v for k, v in data["quality"].items() if k != "ok"}
        quality["glare_boxes"] = [tuple(b) for b in quality.get("glare_boxes", [])]
        return cls(
            width=data["width"],
            height=data["height"],
            quality=QualityReport(**quality),
            display=text_read_from_dict(data["display"]),
            serial=text_read_from_dict(data["serial"]),
            serial_status=data["serial_status"],
            texts=[r for r in map(text_read_from_dict, data.get("texts", [])) if r],
            timings_ms=data.get("timings_ms", {}),
        )


def text_read_from_dict(data: dict[str, Any] | None) -> TextRead | None:
    if not data:
        return None
    fields = {k: v for k, v in data.items() if k != "unclear_positions"}
    return TextRead(**fields)


def _digit_share(text: str) -> float:
    return sum(c.isdigit() for c in text) / len(text) if text else 0.0


def _merge(old: TextRead, new: Recognition, source: str) -> TextRead:
    if len(new.text) != len(old.text):
        if new.text and min(new.confidences) > old.confidence:
            return replace(old, text=new.text, confidences=new.confidences, source=source)
        return old
    chars, confs = [], []
    for i, (a, b) in enumerate(zip(old.text, new.text, strict=True)):
        if new.confidences[i] > old.confidences[i]:
            chars.append(b)
            confs.append(new.confidences[i])
        else:
            chars.append(a)
            confs.append(old.confidences[i])
    return replace(old, text="".join(chars), confidences=confs, source=f"{old.source}+{source}")


class MeterReader:
    def __init__(self, models_dir: Path) -> None:
        self._detector = TextDetector(models_dir)
        self._recognizer = TextRecognizer(models_dir)
        self._lock = threading.Lock()

    def analyze(self, image: Image, expected_serial: str | None = None) -> Analysis:
        with self._lock:
            return self._analyze(image, expected_serial)

    def _analyze(self, image: Image, expected_serial: str | None) -> Analysis:
        timings: dict[str, float] = {}
        started = time.perf_counter()

        def lap(name: str) -> None:
            nonlocal started
            now = time.perf_counter()
            timings[name] = round((now - started) * 1000, 1)
            started = now

        quality = assess(image)
        lap("quality")
        quads = self._detector.detect(image)
        lap("detect")

        reads: list[tuple[TextRead, TextRead]] = []
        for quad in quads:
            logits = self._recognizer.logits(straighten(image, quad))
            general = decode(logits)
            digits = decode(logits, DIGITS)
            height = quad_height(quad)
            reads.append(
                (
                    TextRead(general.text, general.confidences, quad, height),
                    TextRead(digits.text, digits.confidences, quad, height),
                )
            )
        lap("recognize")

        display = self._pick_display(image, reads)
        lap("display")
        serial, status = self._pick_serial(reads, display, expected_serial)
        lap("serial")

        h, w = image.shape[:2]
        return Analysis(
            w, h, quality, display, serial, status, [general for general, _ in reads], timings
        )

    def reread(self, image: Image, display: TextRead, variant: str) -> TextRead:
        crop = variants.apply(variant, straighten(image, display.quad))
        with self._lock:
            recognition = self._recognizer.read(crop, DIGITS)
        return _merge(display, recognition, variant)

    def _pick_display(
        self, image: Image, reads: list[tuple[TextRead, TextRead]]
    ) -> TextRead | None:
        candidates = [
            digits
            for general, digits in reads
            if _digit_share(general.text) >= 0.8
            and DISPLAY_MIN_DIGITS <= len(digits.text) <= DISPLAY_MAX_DIGITS
        ]
        if not candidates:
            return None
        display = max(candidates, key=lambda r: r.height)
        if display.unclear_positions:
            backup = sevenseg.decode(straighten(image, display.quad))
            if backup:
                display = _merge(display, backup, "sevenseg")
        return display

    def _pick_serial(
        self, reads: list[tuple[TextRead, TextRead]], display: TextRead | None, expected: str | None
    ) -> tuple[TextRead | None, SerialStatus]:
        others = [
            general for general, _ in reads if display is None or general.quad != display.quad
        ]
        if expected:
            for read in others:
                if serials.matches(read.text, expected):
                    return read, "match"
        candidates = [r for r in others if serials.looks_like_serial(r.text)]
        if not candidates:
            return None, "unreadable"
        best = max(candidates, key=lambda r: (r.confidence, len(r.text)))
        if best.confidence < SERIAL_MIN_CONFIDENCE:
            return best, "unreadable"
        return best, "mismatch" if expected else "read"


def load_image(path: Path) -> Image:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"not an image: {path}")
    return image


def decode_image(data: bytes) -> Image | None:
    buffer = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR) if buffer.size else None
    if image is None or image.ndim != 3 or min(image.shape[:2]) < 200:
        return None
    return image
