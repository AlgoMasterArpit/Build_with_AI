from __future__ import annotations

from app.vision.pipeline import MeterReader
from tests.vision import synth


def test_reads_display_and_matches_serial(reader: MeterReader) -> None:
    analysis = reader.analyze(synth.meter_photo("01910", "SN 48217"), expected_serial="48217")
    assert analysis.display is not None
    assert analysis.display.text == "01910"
    assert not analysis.display.unclear_positions
    assert analysis.serial_status == "match"


def test_other_meter_is_a_mismatch(reader: MeterReader) -> None:
    analysis = reader.analyze(synth.meter_photo("01910", "SN 51930"), expected_serial="48217")
    assert analysis.serial_status == "mismatch"
    assert analysis.serial is not None


def test_add_meter_mode_reads_unknown_serial(reader: MeterReader) -> None:
    analysis = reader.analyze(synth.meter_photo("01910", "SN 51930"))
    assert analysis.serial_status == "read"


def test_half_turned_digit_is_unclear(reader: MeterReader) -> None:
    analysis = reader.analyze(synth.meter_photo("01910", half=3), expected_serial="48217")
    assert analysis.display is not None
    assert 3 in analysis.display.unclear_positions


def test_reread_never_lowers_confidence(reader: MeterReader) -> None:
    photo = synth.meter_photo("01910", half=3)
    display = reader.analyze(photo).display
    assert display is not None
    again = reader.reread(photo, display, "clahe")
    assert all(n >= o for n, o in zip(again.confidences, display.confidences, strict=True))


def test_analysis_serialises(reader: MeterReader) -> None:
    data = reader.analyze(synth.meter_photo()).to_dict()
    assert data["display"]["text"] == "01910"
    assert data["quality"]["ok"] is True
