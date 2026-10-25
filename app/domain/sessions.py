from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Mode(StrEnum):
    READING = "reading"
    ADD_METER = "add_meter"


class Counters(BaseModel):
    bad_photo: int = 0
    mismatch: int = 0
    unreadable_serial: int = 0
    unclear_photos: int = 0


class Session(BaseModel):
    session_id: str
    hostel_id: str
    room_id: str
    round_id: str
    mode: Mode
    expires_at: int
    counters: Counters = Field(default_factory=Counters)
    photo_keys: list[str] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    responses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    pending_meter: dict[str, Any] | None = None
    closed: bool = False

    def expired(self, now: int) -> bool:
        return now >= self.expires_at
