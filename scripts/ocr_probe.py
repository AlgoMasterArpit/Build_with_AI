"""Run the vision pipeline on a folder of meter photos and write annotated copies.

usage: uv run python scripts/ocr_probe.py PHOTOS_DIR [--expected SERIAL] [--out probe_out]

If a file name contains a run of 4+ digits (e.g. water_004521.jpg) it is treated as the
true reading and the probe reports whether the display was read correctly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.vision.geometry import Image
from app.vision.pipeline import DIGIT_CONFIDENCE_THRESHOLD, Analysis, MeterReader, load_image

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png"}
GREEN, YELLOW, RED, BLUE, GREY = (
    (80, 200, 80),
    (0, 200, 255),
    (60, 60, 230),
    (230, 160, 40),
    (160, 160, 160),
)


def annotate(image: Image, analysis: Analysis) -> Image:
    out = image.copy()
    thickness = max(2, image.shape[1] // 500)
    font_scale = image.shape[1] / 1400
    for box in analysis.quality.glare_boxes:
        cv2.rectangle(out, box[:2], box[2:], RED, thickness)
    for read in analysis.texts:
        cv2.polylines(out, [np.array(read.quad)], True, GREY, thickness)
    if analysis.serial:
        color = GREEN if analysis.serial_status in ("match", "read") else RED
        cv2.polylines(out, [np.array(analysis.serial.quad)], True, color, thickness * 2)
        x, y = analysis.serial.quad[0]
        cv2.putText(
            out,
            f"SN {analysis.serial.text} ({analysis.serial_status})",
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
        )
    if analysis.display:
        display = analysis.display
        color = YELLOW if display.unclear_positions else GREEN
        cv2.polylines(out, [np.array(display.quad)], True, color, thickness * 2)
        x, y = display.quad[3]
        label = " ".join(
            f"{c}:{p:.2f}" for c, p in zip(display.text, display.confidences, strict=True)
        )
        cv2.putText(
            out,
            label,
            (x, y + int(40 * font_scale)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
        )
    return out


def truth_from_name(path: Path) -> str | None:
    runs = re.findall(r"\d{4,}", path.stem)
    return runs[-1] if runs else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("photos", type=Path)
    parser.add_argument("--expected", help="registered serial to check against")
    parser.add_argument("--out", type=Path, default=Path("probe_out"))
    parser.add_argument("--models", type=Path, default=Path("models"))
    args = parser.parse_args()

    reader = MeterReader(args.models)
    args.out.mkdir(parents=True, exist_ok=True)
    photos = sorted(p for p in args.photos.iterdir() if p.suffix.lower() in PHOTO_SUFFIXES)
    correct = scored = 0
    for path in photos:
        image = load_image(path)
        analysis = reader.analyze(image, args.expected)
        if analysis.display and analysis.display.unclear_positions:
            analysis = _with_reread(reader, image, analysis)
        cv2.imwrite(str(args.out / f"{path.stem}_probe.jpg"), annotate(image, analysis))
        (args.out / f"{path.stem}.json").write_text(json.dumps(analysis.to_dict(), indent=2))

        display = analysis.display
        truth = truth_from_name(path)
        verdict = ""
        if truth and display:
            scored += 1
            ok = display.text == truth
            correct += ok
            verdict = "  RIGHT" if ok else f"  WRONG (truth {truth})"
        reading = (
            f"{display.text} min_conf={display.confidence:.2f} unclear={display.unclear_positions}"
            if display
            else "no display found"
        )
        serial = (
            f"{analysis.serial.text}:{analysis.serial_status}"
            if analysis.serial
            else analysis.serial_status
        )
        size = f"{image.shape[1]}x{image.shape[0]}"
        elapsed = sum(analysis.timings_ms.values())
        print(
            f"{path.name:32} {size} issues={analysis.quality.issues or '-'} "
            f"display={reading}{verdict} serial={serial} ms={elapsed:.0f}"
        )
    if scored:
        print(f"\ndisplay accuracy: {correct}/{scored}  (threshold {DIGIT_CONFIDENCE_THRESHOLD})")
    print(f"annotated images: {args.out.resolve()}")


def _with_reread(reader: MeterReader, image: Image, analysis: Analysis) -> Analysis:
    from dataclasses import replace

    display = analysis.display
    assert display is not None
    for variant in ("clahe", "upscale", "threshold", "invert"):
        display = reader.reread(image, display, variant)
        if not display.unclear_positions:
            break
    return replace(analysis, display=display)


if __name__ == "__main__":
    main()
