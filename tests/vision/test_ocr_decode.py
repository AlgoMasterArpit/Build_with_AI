from __future__ import annotations

import numpy as np

from app.vision.ocr import CHARSET, DIGITS, decode

BLANK = 0


def logits_for(path: list[int | tuple[int, int]]) -> np.ndarray:
    out = np.full((len(path), len(CHARSET) + 1), -5.0, np.float32)
    for step, index in enumerate(path):
        if isinstance(index, tuple):
            out[step, index[0]] = 5.0
            out[step, index[1]] = 4.8
        else:
            out[step, index] = 10.0
    return out


def idx(ch: str) -> int:
    return CHARSET.index(ch) + 1


def test_ctc_collapses_repeats_and_blanks() -> None:
    result = decode(logits_for([idx("1"), idx("1"), BLANK, idx("1"), idx("2")]))
    assert result.text == "112"
    assert all(c > 0.99 for c in result.confidences)


def test_split_vote_gives_low_confidence() -> None:
    result = decode(logits_for([idx("3"), BLANK, (idx("3"), idx("4"))]), DIGITS)
    assert result.text == "33"
    assert result.confidences[1] < 0.6


def test_digit_charset_ignores_letters() -> None:
    result = decode(logits_for([idx("o"), BLANK, idx("7")]), DIGITS)
    assert result.text.isdigit() or result.text == ""
