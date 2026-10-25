from __future__ import annotations

import pytest

from app.vision.serials import last4, looks_like_serial, matches, normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("sn48217", "48217"), ("S/N: 48-217", "48217"), ("no.o4821l", "048211")],
)
def test_normalize_strips_prefix_and_lookalikes(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_matches_tolerates_one_slip_on_long_serials() -> None:
    assert matches("sn0048217", "0048217")
    assert matches("0O48Z17", "0048217")
    assert matches("0048217x", "0048217")
    assert not matches("0048218", "48217")


def test_short_serials_must_match_exactly() -> None:
    assert matches("48217", "48217")
    assert not matches("48218", "48217")


def test_serial_shape() -> None:
    assert looks_like_serial("SN 48217")
    assert not looks_like_serial("kwh")
    assert last4("SN-0048217") == "8217"
