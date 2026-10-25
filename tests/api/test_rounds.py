from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.rounds import RoomStatus, RoundState
from app.store.table import Table


def test_round_lists_rooms_with_status(client: TestClient) -> None:
    body = client.get("/api/round").json()
    assert body["hostel_name"] == "Hostel A"
    assert body["progress"] == {"done": 0, "total": 12}
    rooms = {r["room_id"]: r for r in body["rooms"]}
    assert rooms["201"] == {"room_id": "201", "serial_last4": "0201", "status": "pending"}
    assert rooms["205"]["status"] == "needs_meter"
    assert list(rooms) == sorted(rooms)


def test_wrong_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/round", headers={"x-round-token": "nope"})
    assert response.status_code == 404
    assert response.json()["error"] == "invalid_link"


def test_missing_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/round", headers={"x-round-token": ""})
    assert response.status_code == 404


def test_room_screen_data(client: TestClient) -> None:
    body = client.get("/api/rooms/201").json()
    assert body["serial"] == "SAMPLE10201"
    assert body["previous_reading"] == "01204"
    assert body["hint"].startswith("Meter ka display")


def test_room_without_meter_gets_add_meter_hint(client: TestClient) -> None:
    body = client.get("/api/rooms/205").json()
    assert body["serial"] is None
    assert body["status"] == "needs_meter"
    assert "serial sticker" in body["hint"]


def test_unknown_room(client: TestClient) -> None:
    assert client.get("/api/rooms/999").json()["error"] == "unknown_room"


def test_last_months_state_reads_as_pending(client: TestClient, table: Table) -> None:
    room = table.get_room("hostel-a", "201")
    assert room is not None
    room.round_state = RoundState(round="2020-01", status=RoomStatus.REVIEW)
    table.put_room(room)
    rooms = {r["room_id"]: r for r in client.get("/api/round").json()["rooms"]}
    assert rooms["201"]["status"] == "pending"


def test_round_page_is_served(client: TestClient) -> None:
    response = client.get("/r/anything")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
