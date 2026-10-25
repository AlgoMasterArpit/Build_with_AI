"""Download the OpenCV Zoo text models into ./models and verify their SHA-256."""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

ZOO = "https://github.com/opencv/opencv_zoo/raw/main/models"

MODELS = {
    "text_detection_en_ppocrv3_2023may.onnx": (
        f"{ZOO}/text_detection_ppocr/text_detection_en_ppocrv3_2023may.onnx",
        "03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587",
    ),
    "text_recognition_CRNN_EN_2021sep.onnx": (
        f"{ZOO}/text_recognition_crnn/text_recognition_CRNN_EN_2021sep.onnx",
        "a84b1f6e11a65c2d733cb0cc1f014aae3f99051e3f11447dc282faa678eee544",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in MODELS.items():
        path = target_dir / name
        if path.exists() and sha256(path) == expected:
            print(f"ok      {name}")
            continue
        partial = path.with_suffix(".part")
        print(f"fetch   {name}")
        urllib.request.urlretrieve(url, partial)
        actual = sha256(partial)
        if actual != expected:
            partial.unlink()
            raise SystemExit(f"checksum mismatch for {name}: {actual}")
        partial.replace(path)


if __name__ == "__main__":
    fetch(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models"))
