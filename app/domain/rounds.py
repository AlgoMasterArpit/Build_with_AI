from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class RoomStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    REVIEW = "review"
    NEEDS_METER = "needs_meter"


class RoundState(BaseModel):
    round: str
    status: RoomStatus
    note: str | None = None


class Room(BaseModel):
    hostel_id: str
    room_id: str
    meter_type: str = "electricity"
    meter_serial: str | None = None
    previous_reading: str | None = None
    previous_at: str | None = None
    round_state: RoundState | None = None


def current_round(now: datetime, tz: str) -> str:
    return now.astimezone(ZoneInfo(tz)).strftime("%Y-%m")


def round_label(round_id: str) -> str:
    return datetime.strptime(round_id, "%Y-%m").strftime("%b %Y")


def status_for(room: Room, round_id: str) -> RoomStatus:
    state = room.round_state
    if state and state.round == round_id:
        return state.status
    return RoomStatus.PENDING if room.meter_serial else RoomStatus.NEEDS_METER
