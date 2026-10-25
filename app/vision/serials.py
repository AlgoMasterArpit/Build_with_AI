from __future__ import annotations

import re

LOOKALIKES = str.maketrans(
    {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
)
PREFIXES = ("SERIALNO", "SERIAL", "SRNO", "MTRNO", "METERNO", "SNO", "SN", "NO")


def normalize(text: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]", "", text).upper()
    for prefix in PREFIXES:
        if cleaned.startswith(prefix) and len(cleaned) - len(prefix) >= 4:
            cleaned = cleaned[len(prefix) :]
            break
    return cleaned.translate(LOOKALIKES)


def _distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def matches(read: str, expected: str) -> bool:
    got, want = normalize(read), normalize(expected)
    if not got or not want:
        return False
    if want in got:
        return True
    allowed = 1 if len(want) >= 6 else 0
    return _distance(got, want) <= allowed


def looks_like_serial(text: str) -> bool:
    value = normalize(text)
    return len(value) >= 5 and sum(ch.isdigit() for ch in value) >= 4


def last4(serial: str) -> str:
    return normalize(serial)[-4:]
