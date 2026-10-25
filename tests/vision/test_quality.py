from __future__ import annotations

from app.vision.quality import assess
from tests.vision import synth


def test_clean_photo_has_no_issues() -> None:
    assert assess(synth.meter_photo()).issues == []


def test_glare_is_located_by_cell() -> None:
    report = assess(synth.with_glare(synth.meter_photo(), cell=(0, 2)))
    assert "glare" in report.issues
    assert "top-right" in report.glare_cells
    assert report.glare_boxes


def test_blur_is_detected() -> None:
    assert "blur" in assess(synth.blurred(synth.meter_photo())).issues


def test_dark_is_detected_instead_of_blur() -> None:
    assert assess(synth.darkened(synth.meter_photo())).issues == ["dark"]
