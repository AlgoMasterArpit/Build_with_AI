from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.sessions import Counters, Mode


class Action(StrEnum):
    RETAKE = "retake"
    REREAD = "reread"
    NEW_PHOTO = "new_photo"
    SAVE = "save"
    CONFIRM = "confirm"
    REVIEW = "review"


class Problem(StrEnum):
    BAD_PHOTO = "bad_photo"
    MISMATCH = "mismatch"
    UNREADABLE_SERIAL = "unreadable_serial"
    UNCLEAR_PHOTOS = "unclear_photos"


LIMITS = {
    Problem.BAD_PHOTO: 3,
    Problem.MISMATCH: 1,
    Problem.UNREADABLE_SERIAL: 3,
    Problem.UNCLEAR_PHOTOS: 1,
}

REVIEW_REASONS = {
    Problem.BAD_PHOTO: "3 koshish ke baad bhi photo saaf nahi aayi.",
    Problem.MISMATCH: "Lagatar 2 baar galat meter ki photo aayi.",
    Problem.UNREADABLE_SERIAL: "Serial number padha nahi gaya.",
    Problem.UNCLEAR_PHOTOS: "Ek digit nayi photo ke baad bhi saaf nahi hua.",
}

REREAD_ORDER = ("clahe", "upscale", "threshold", "invert")

ROW_WORDS = {"top": "Upar", "middle": "Beech", "bottom": "Neeche"}
COL_WORDS = {"left": "left", "center": "beech", "right": "right"}


@dataclass(frozen=True)
class Observation:
    mode: Mode
    room_id: str
    quality_issues: list[str]
    glare_cells: list[str]
    serial_status: str
    serial_text: str | None
    expected_last4: str | None
    display_text: str | None
    display_confidences: list[float]
    unclear_positions: list[int]
    rereads_done: list[str]
    counters: Counters
    linked_room: str | None = None

    @property
    def problem(self) -> Problem | None:
        if self.quality_issues or self.display_text is None:
            return Problem.BAD_PHOTO
        if self.linked_room or (self.mode == Mode.READING and self.serial_status == "mismatch"):
            return Problem.MISMATCH
        if self.serial_status == "unreadable":
            return Problem.UNREADABLE_SERIAL
        if self.unclear_positions and self.rereads_done:
            return Problem.UNCLEAR_PHOTOS
        return None

    def attempts_left(self) -> dict[str, int]:
        used = self.counters.model_dump()
        return {p.value: max(0, LIMITS[p] - used[p.value]) for p in Problem}

    def to_prompt(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "room": self.room_id,
            "quality_issues": self.quality_issues,
            "glare_cells": self.glare_cells,
            "serial": {
                "status": self.serial_status,
                "expected_last4": self.expected_last4,
                "linked_to_other_room": self.linked_room,
            },
            "display": {
                "found": self.display_text is not None,
                "digit_confidences": self.display_confidences,
                "unclear_positions": self.unclear_positions,
                "rereads_done": self.rereads_done,
            },
            "attempts_left": self.attempts_left(),
        }


@dataclass(frozen=True)
class Decision:
    action: Action
    hint: str
    reason: str
    problem: Problem | None = None
    variant: str | None = None
    decided_by: str = "rule"
    notes: list[str] = field(default_factory=list)


def _over_limit(obs: Observation, problem: Problem) -> bool:
    used: int = getattr(obs.counters, problem.value)
    return used >= LIMITS[problem]


def allowed_actions(obs: Observation) -> list[Action]:
    problem = obs.problem
    if problem is not None:
        if _over_limit(obs, problem):
            return [Action.REVIEW]
        retry = Action.NEW_PHOTO if problem == Problem.UNCLEAR_PHOTOS else Action.RETAKE
        return [retry, Action.REVIEW]
    if obs.unclear_positions:
        return [Action.REREAD]
    return [Action.CONFIRM if obs.mode == Mode.ADD_METER else Action.SAVE]


def next_variant(obs: Observation) -> str | None:
    return next((v for v in REREAD_ORDER if v not in obs.rereads_done), None)


def glare_hint(cells: list[str]) -> str:
    row, col = cells[0].split("-")
    place = ROW_WORDS[row] if col == "center" else f"{ROW_WORDS[row]} {COL_WORDS[col]}"
    tilt = {"right": "phone thoda left tilt karo", "left": "phone thoda right tilt karo"}.get(
        col, "phone ka angle thoda badlo"
    )
    return f"{place} mein glare hai, {tilt}."


def problem_hint(obs: Observation, problem: Problem) -> str:
    if problem == Problem.BAD_PHOTO:
        if "glare" in obs.quality_issues and obs.glare_cells:
            return glare_hint(obs.glare_cells)
        if "dark" in obs.quality_issues:
            return "Andhera hai, torch ya light on karke dobara lo."
        if "blur" in obs.quality_issues:
            return "Photo dhundhli hai, phone sthir rakh ke dobara lo."
        return "Display nahi dikha, meter ko frame ke beech mein lo."
    if problem == Problem.MISMATCH:
        if obs.linked_room:
            other, room = obs.linked_room, obs.room_id
            return f"Ye meter Room {other} se juda hai. Room {room} ka meter dhoondho."
        return f"Ye Room {obs.room_id} ka meter nahi hai, board pe …{obs.expected_last4} dhoondho."
    if problem == Problem.UNREADABLE_SERIAL:
        return "Serial number nahi padh paaye. Sticker ko frame ke beech mein lo, chamak se bachao."
    return "Ek digit saaf nahi hai, thoda paas se dobara lo."


def decide(obs: Observation) -> Decision:
    problem = obs.problem
    if problem is not None:
        if _over_limit(obs, problem):
            return Decision(Action.REVIEW, REVIEW_REASONS[problem], problem.value, problem)
        retry = Action.NEW_PHOTO if problem == Problem.UNCLEAR_PHOTOS else Action.RETAKE
        return Decision(retry, problem_hint(obs, problem), problem.value, problem)
    if obs.unclear_positions:
        variant = next_variant(obs)
        if variant:
            return Decision(
                Action.REREAD,
                "Ek digit saaf nahi, dobara padh raha hoon.",
                "unclear_digit",
                variant=variant,
            )
    if obs.mode == Mode.ADD_METER:
        return Decision(Action.CONFIRM, "Serial aur reading padh li.", "ready_to_confirm")
    return Decision(Action.SAVE, "Reading saaf hai.", "clear_reading")
