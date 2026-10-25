from __future__ import annotations

import secrets
from typing import Any

from app.domain.rounds import Room
from app.store.table import Table


def seed_hostel(table: Table, data: dict[str, Any], token: str | None = None) -> str:
    hostel_id = data["hostel_id"]
    table.put_hostel(hostel_id, data["name"])
    for room in data["rooms"]:
        if table.get_room(hostel_id, room["room_id"]) is None:
            table.put_room(
                Room(hostel_id=hostel_id, meter_type=data.get("meter_type", "electricity"), **room)
            )
    token = token or secrets.token_urlsafe(32)
    table.put_link(token, hostel_id, data.get("caretaker", ""))
    return token
