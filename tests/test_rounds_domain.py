from __future__ import annotations

from datetime import UTC, datetime

from app.domain.rounds import Room, RoomStatus, RoundState, current_round, round_label, status_for


def test_round_uses_india_time() -> None:
    assert current_round(datetime(2026, 10, 31, 20, 0, tzinfo=UTC), "Asia/Kolkata") == "2026-11"
    assert round_label("2026-10") == "Oct 2026"


def test_status_for_current_and_old_rounds() -> None:
    room = Room(hostel_id="h", room_id="1", meter_serial="X1")
    assert status_for(room, "2026-10") == RoomStatus.PENDING
    room.round_state = RoundState(round="2026-10", status=RoomStatus.DONE)
    assert status_for(room, "2026-10") == RoomStatus.DONE
    assert status_for(room, "2026-11") == RoomStatus.PENDING
    assert status_for(Room(hostel_id="h", room_id="2"), "2026-10") == RoomStatus.NEEDS_METER
