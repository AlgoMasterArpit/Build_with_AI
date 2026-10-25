from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import RoundDep, TableDep
from app.api.errors import UNKNOWN_ROOM
from app.domain.rounds import RoomStatus, round_label, status_for
from app.vision.serials import last4

router = APIRouter(prefix="/api")

READING_HINT = "Meter ka display aur serial number dono frame mein rakho."
ADD_METER_HINT = "Meter ka serial sticker aur display dono frame mein rakho."


class RoomRow(BaseModel):
    room_id: str
    serial_last4: str | None
    status: RoomStatus


class Progress(BaseModel):
    done: int
    total: int


class RoundView(BaseModel):
    hostel_name: str
    caretaker: str
    round_id: str
    round_label: str
    progress: Progress
    rooms: list[RoomRow]


class RoomView(BaseModel):
    room_id: str
    meter_type: str
    serial: str | None
    serial_last4: str | None
    previous_reading: str | None
    previous_at: str | None
    status: RoomStatus
    hint: str


@router.get("/round")
def get_round(ctx: RoundDep, table: TableDep) -> RoundView:
    rooms = table.list_rooms(ctx.hostel_id)
    rows = [
        RoomRow(
            room_id=r.room_id,
            serial_last4=last4(r.meter_serial) if r.meter_serial else None,
            status=status_for(r, ctx.round_id),
        )
        for r in rooms
    ]
    return RoundView(
        hostel_name=table.get_hostel_name(ctx.hostel_id) or ctx.hostel_id,
        caretaker=ctx.caretaker,
        round_id=ctx.round_id,
        round_label=round_label(ctx.round_id),
        progress=Progress(done=sum(r.status == RoomStatus.DONE for r in rows), total=len(rows)),
        rooms=rows,
    )


@router.get("/rooms/{room_id}")
def get_room(room_id: str, ctx: RoundDep, table: TableDep) -> RoomView:
    room = table.get_room(ctx.hostel_id, room_id)
    if room is None:
        raise UNKNOWN_ROOM
    return RoomView(
        room_id=room.room_id,
        meter_type=room.meter_type,
        serial=room.meter_serial,
        serial_last4=last4(room.meter_serial) if room.meter_serial else None,
        previous_reading=room.previous_reading,
        previous_at=room.previous_at,
        status=status_for(room, ctx.round_id),
        hint=READING_HINT if room.meter_serial else ADD_METER_HINT,
    )
