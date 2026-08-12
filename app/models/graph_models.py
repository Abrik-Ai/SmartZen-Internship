from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ScheduleLookupArgs(BaseModel):
    range_value: Literal["today", "week", "upcoming"]


class FindFreeRoomsArgs(BaseModel):
    minutes_needed: int
    start_time: str | None = None


class GetRoomStatusArgs(BaseModel):
    pass


class DocumentationSearchArgs(BaseModel):
    query: str


class GetMyScheduleToolCall(BaseModel):
    name: Literal["get_my_schedule"]
    args: ScheduleLookupArgs


class FindFreeRoomsToolCall(BaseModel):
    name: Literal["find_free_rooms"]
    args: FindFreeRoomsArgs


class GetRoomStatusToolCall(BaseModel):
    name: Literal["get_room_status"]
    args: GetRoomStatusArgs


class DocumentationSearchToolCall(BaseModel):
    name: Literal["documentation_search"]
    args: DocumentationSearchArgs


ToolCall = Annotated[
    GetMyScheduleToolCall
    | FindFreeRoomsToolCall
    | GetRoomStatusToolCall
    | DocumentationSearchToolCall,
    Field(discriminator="name"),
]


class GraphResponse(BaseModel):
    reply: str
    toolCall: ToolCall | None = None