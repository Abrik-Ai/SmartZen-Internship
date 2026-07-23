from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ControlProposal(BaseModel):
    kind: Literal["control"] = "control"
    room_id: str
    device: str
    on: bool
    label: str

class ExtendProposal(BaseModel):
    kind: Literal["extend"] = "extend"
    session_id: str
    until: datetime
    label: str

class EndSessionProposal(BaseModel):
    kind: Literal["end_session"] = "end_session"
    session_id: str
    label: str

class RoomChangeProposal(BaseModel):
    kind: Literal["room_change"] = "room_change"
    to_room_id: str
    to_room_name: str
    minutes: int | None = None
    note: str | None = None
    label: str