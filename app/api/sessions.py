from __future__ import annotations

import json
import time
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from app.agent.loop import Agent, AgentRun, RuleDecider
from app.agent.policy import Action
from app.api.deps import RoundContext, RoundDep, SettingsDep, TableDep
from app.api.errors import UNKNOWN_ROOM, ApiError
from app.domain.sessions import Mode, Session
from app.store.photos import PhotoStore
from app.vision.client import build_vision
from app.vision.geometry import split_quad
from app.vision.pipeline import DIGIT_CONFIDENCE_THRESHOLD, decode_image

router = APIRouter(prefix="/api")

SESSION_GONE = ApiError(404, "session_expired", "Session purana ho gaya, room dobara kholo.")
NOT_A_PHOTO = ApiError(422, "not_a_photo", "Photo padh nahi paaye, dobara lo.")
TOO_LARGE = ApiError(413, "photo_too_large", "Photo bahut badi hai, dobara lo.")


class SessionCreated(BaseModel):
    session_id: str
    mode: Mode


def get_agent(request: Request) -> Agent:
    agent: Agent | None = getattr(request.app.state, "agent", None)
    if agent is None:
        settings = request.app.state.settings
        agent = Agent(build_vision(settings.models_dir, settings.vision_url), RuleDecider())
        request.app.state.agent = agent
    return agent


def _photos(request: Request) -> PhotoStore:
    store: PhotoStore = request.app.state.photos
    return store


def _session(table: TableDep, ctx: RoundContext, session_id: str) -> Session:
    session = table.get_session(session_id, int(time.time()))
    if session is None or session.hostel_id != ctx.hostel_id or session.closed:
        raise SESSION_GONE
    return session


@router.post("/rooms/{room_id}/sessions")
def start_session(
    room_id: str, ctx: RoundDep, table: TableDep, settings: SettingsDep
) -> SessionCreated:
    room = table.get_room(ctx.hostel_id, room_id)
    if room is None:
        raise UNKNOWN_ROOM
    session = Session(
        session_id=uuid.uuid4().hex,
        hostel_id=ctx.hostel_id,
        room_id=room_id,
        round_id=ctx.round_id,
        mode=Mode.READING if room.meter_serial else Mode.ADD_METER,
        expires_at=int(time.time()) + settings.session_ttl_hours * 3600,
    )
    table.put_session(session)
    return SessionCreated(session_id=session.session_id, mode=session.mode)


def _view(run: AgentRun) -> dict[str, Any]:
    analysis, decision = run.analysis, run.decision
    display = analysis.display
    marks = [{"kind": "glare", "box": list(b)} for b in analysis.quality.glare_boxes]
    return {
        "action": decision.action.value,
        "hint": decision.hint,
        "reason": decision.reason,
        "decided_by": decision.decided_by,
        "image": {"width": analysis.width, "height": analysis.height},
        "marks": marks,
        "display": {
            "text": display.text,
            "confidences": display.confidences,
            "digit_quads": split_quad(display.quad, len(display.text)) if display.text else [],
            "unclear_positions": display.unclear_positions,
            "threshold": DIGIT_CONFIDENCE_THRESHOLD,
        }
        if display
        else None,
        "serial": {
            "text": analysis.serial.text.upper(),
            "quad": analysis.serial.quad,
            "status": analysis.serial_status,
        }
        if analysis.serial
        else None,
        "reading": display.text if display and decision.action == Action.SAVE else None,
        "steps": run.steps,
    }


@router.post("/sessions/{session_id}/photos")
def submit_photo(
    session_id: str,
    request: Request,
    ctx: RoundDep,
    table: TableDep,
    settings: SettingsDep,
    photo: Annotated[UploadFile, File()],
    client_photo_id: Annotated[str, Form(min_length=8, max_length=64)],
    location: Annotated[str, Form()] = "{}",
) -> dict[str, Any]:
    session = _session(table, ctx, session_id)
    if client_photo_id in session.responses:
        return session.responses[client_photo_id]

    data = photo.file.read(settings.max_photo_bytes + 1)
    if len(data) > settings.max_photo_bytes:
        raise TOO_LARGE
    image = decode_image(data)
    if image is None:
        raise NOT_A_PHOTO

    room = table.get_room(ctx.hostel_id, session.room_id)
    if room is None:
        raise UNKNOWN_ROOM

    index = len(session.photo_keys) + 1
    key = f"hostel/{ctx.hostel_id}/{session.round_id}/{session.room_id}/{session_id}/{index}.jpg"
    place = _location(location)
    _photos(request).put(
        key,
        data,
        {
            "server-time": str(int(time.time())),
            "session-id": session_id,
            "client-photo-id": client_photo_id,
            "location": place,
        },
    )
    session.photo_keys.append(key)

    run = get_agent(request).run(image, session, room.meter_serial)
    view = _view(run)
    view["photo"] = {
        "index": index,
        "location": place,
        "resolution": f"{image.shape[1]}x{image.shape[0]}",
    }
    session.trace.extend({"photo": index, **s} for s in run.steps)
    session.responses[client_photo_id] = view
    table.put_session(session)
    return view


def _location(raw: str) -> str:
    try:
        data = json.loads(raw)
        lat, lon = float(data["lat"]), float(data["lon"])
        return f"{lat:.6f},{lon:.6f},{float(data.get('accuracy', 0)):.0f}"
    except (ValueError, KeyError, TypeError):
        return "nahi mili"
