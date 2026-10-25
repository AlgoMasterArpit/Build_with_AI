from __future__ import annotations

import io
import uuid
from typing import Any

import cv2
import pytest
from fastapi.testclient import TestClient

from app.domain.rounds import Room
from app.store.table import Table
from app.vision.geometry import Image
from tests.vision import synth

pytestmark = pytest.mark.usefixtures("models_ready")


def jpeg(image: Image) -> bytes:
    ok, data = cv2.imencode(".jpg", image)
    assert ok
    return data.tobytes()


@pytest.fixture
def room_205(table: Table) -> None:
    table.put_room(
        Room(
            hostel_id="hostel-a",
            room_id="205",
            meter_serial="48217",
            previous_reading="01890",
            previous_at="2026-10-26",
        )
    )


def session(client: TestClient, room: str = "205") -> str:
    response = client.post(f"/api/rooms/{room}/sessions")
    assert response.status_code == 200
    return str(response.json()["session_id"])


def send(client: TestClient, sid: str, image: bytes, photo_id: str | None = None) -> Any:
    response = client.post(
        f"/api/sessions/{sid}/photos",
        files={"photo": ("p.jpg", io.BytesIO(image), "image/jpeg")},
        data={"client_photo_id": photo_id or uuid.uuid4().hex},
    )
    assert response.status_code == 200, response.text
    return response.json()


def meter(**kwargs: Any) -> Image:
    return synth.meter_photo(serial="SN 48217", **kwargs)


@pytest.mark.usefixtures("room_205")
def test_glare_photo_gets_retake_hint(client: TestClient) -> None:
    body = send(client, session(client), jpeg(synth.with_glare(meter())))
    assert body["action"] == "retake"
    assert "glare" in body["hint"]
    assert body["marks"][0]["kind"] == "glare"
    assert [s["step"] for s in body["steps"]] == ["perceive", "decide"]


@pytest.mark.usefixtures("room_205")
def test_clear_photo_is_read_with_digit_boxes(client: TestClient) -> None:
    body = send(client, session(client), jpeg(meter(reading="01910")))
    assert body["action"] == "save"
    assert body["reading"] == "01910"
    assert len(body["display"]["digit_quads"]) == 5
    assert body["serial"]["status"] == "match"
    assert body["photo"]["location"] == "nahi mili"


@pytest.mark.usefixtures("room_205")
def test_half_turned_digit_is_reread_before_deciding(client: TestClient) -> None:
    body = send(client, session(client), jpeg(meter(reading="01910", half=3)))
    assert [s["step"] for s in body["steps"]] == ["perceive", "decide", "reread", "decide"]
    assert body["action"] in ("new_photo", "save")


@pytest.mark.usefixtures("room_205")
def test_same_client_photo_id_returns_the_first_answer(client: TestClient) -> None:
    sid = session(client)
    first = send(client, sid, jpeg(synth.blurred(meter())), "photo-0001")
    again = send(client, sid, jpeg(meter()), "photo-0001")
    assert again == first


@pytest.mark.usefixtures("room_205")
def test_bad_photos_count_up_to_review(client: TestClient) -> None:
    sid = session(client)
    blurry = jpeg(synth.blurred(meter()))
    actions = [send(client, sid, blurry)["action"] for _ in range(4)]
    assert actions == ["retake", "retake", "retake", "review"]


def test_not_a_photo_is_rejected(client: TestClient) -> None:
    sid = session(client, "201")
    response = client.post(
        f"/api/sessions/{sid}/photos",
        files={"photo": ("p.jpg", io.BytesIO(b"not an image"), "image/jpeg")},
        data={"client_photo_id": "photo-0002"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "not_a_photo"


def test_unknown_session(client: TestClient) -> None:
    response = client.post(
        "/api/sessions/nope/photos",
        files={"photo": ("p.jpg", io.BytesIO(b"x"), "image/jpeg")},
        data={"client_photo_id": "photo-0003"},
    )
    assert response.json()["error"] == "session_expired"


def test_room_without_meter_starts_add_meter_session(client: TestClient) -> None:
    assert client.post("/api/rooms/204/sessions").json()["mode"] == "add_meter"
