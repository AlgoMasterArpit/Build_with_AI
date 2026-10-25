from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Request

from app.api.errors import INVALID_LINK
from app.config import Settings
from app.domain.rounds import current_round
from app.store.table import Table


@dataclass(frozen=True)
class RoundContext:
    hostel_id: str
    caretaker: str
    round_id: str


def get_table(request: Request) -> Table:
    table: Table = request.app.state.table
    return table


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def round_context(
    table: Annotated[Table, Depends(get_table)],
    settings: Annotated[Settings, Depends(get_settings)],
    x_round_token: Annotated[str | None, Header()] = None,
) -> RoundContext:
    link = table.get_link(x_round_token) if x_round_token else None
    if not link:
        raise INVALID_LINK
    return RoundContext(
        hostel_id=str(link["hostel_id"]),
        caretaker=str(link.get("caretaker", "")),
        round_id=current_round(datetime.now(UTC), settings.timezone),
    )


TableDep = Annotated[Table, Depends(get_table)]
RoundDep = Annotated[RoundContext, Depends(round_context)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
