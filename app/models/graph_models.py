from typing import Literal

from pydantic import BaseModel


class ScheduleLookup(BaseModel):
    range: Literal["today", "week", "upcoming"]


class GraphResponse(BaseModel):
    reply: str
    scheduleLookup: ScheduleLookup | None