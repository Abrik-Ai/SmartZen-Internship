"""
Proposal tools: extend session, end session, change room.

None of these tools mutate backend state. Each one reads existing
state through `BackendClient`'s read-only methods (`get_active_sessions`,
`get_empty_rooms`) and returns a proposal object describing an action a
human still has to confirm elsewhere. There is no write path here at
all - no "extend", "end", or "change room" method exists on
`BackendClient`, so these tools are structurally incapable of
performing the action themselves.

When a proposal can't be built (no active session, room name doesn't
resolve), the tools return a small result object explaining why instead
of raising or fabricating a proposal that doesn't make sense.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast

from pydantic import BaseModel

from app.backend_client import BackendClient
from app.models.proposals import EndSessionProposal, ExtendProposal, RoomChangeProposal

# Used to search for a free room by name when no explicit duration is given.
DEFAULT_ROOM_SEARCH_MINUTES = 60


class NoActiveSessionResult(BaseModel):
    """Returned instead of a proposal when there's no session to act on."""

    kind: Literal["no_active_session"] = "no_active_session"
    message: str


class RoomNotFoundResult(BaseModel):
    """Returned instead of a proposal when the requested room can't be resolved."""

    kind: Literal["room_not_found"] = "room_not_found"
    requested_name: str
    message: str
    suggestion: Literal["search_free_rooms"] = "search_free_rooms"


async def _get_active_session(token: str, client: BackendClient) -> dict[str, Any] | None:
    """Return the caller's first active session, or None if there isn't one."""

    sessions = await client.get_active_sessions(token)
    active = sessions.get("sessions") if sessions else None

    if not active:
        return None

    return cast(dict[str, Any], active[0])


def _parse_datetime(value: Any) -> datetime | None:
    """Best-effort parse of a backend timestamp into an aware UTC datetime."""

    if not value:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed


async def propose_extend(
    minutes_requested: int,
    token: str,
    client: BackendClient,
) -> ExtendProposal | NoActiveSessionResult:
    """
    Turn "I need N more minutes" into an ExtendProposal.

    The new end time is the later of the session's scheduled end or now,
    plus `minutes_requested`. This only builds the proposal - it never
    calls anything that actually extends the session.

    Args:
        minutes_requested: How many extra minutes were asked for.
        token: User authentication token.
        client: Backend client instance.

    Returns:
        An ExtendProposal, or a NoActiveSessionResult if there's nothing
        to extend right now.
    """
    session = await _get_active_session(token, client)

    if session is None:
        return NoActiveSessionResult(
            message="You don't have an active session right now, so there's nothing to extend."
        )

    now = datetime.now(UTC)
    scheduled_end = _parse_datetime(session.get("end_time"))
    base = max(scheduled_end, now) if scheduled_end is not None else now
    until = base + timedelta(minutes=minutes_requested)

    until_label = until.strftime("%H:%M")

    return ExtendProposal(
        session_id=session.get("id", ""),
        until=until,
        label=f"Extend your session by {minutes_requested} minutes, until {until_label}?",
    )


async def propose_end_session(
    token: str,
    client: BackendClient,
) -> EndSessionProposal | NoActiveSessionResult:
    """
    Turn "I'm done" into an EndSessionProposal.

    Args:
        token: User authentication token.
        client: Backend client instance.

    Returns:
        An EndSessionProposal, or a NoActiveSessionResult explaining
        there's nothing active to end, rather than proposing something
        nonsensical.
    """
    session = await _get_active_session(token, client)

    if session is None:
        return NoActiveSessionResult(
            message="You don't have an active session right now, so there's nothing to end."
        )

    room_id = session.get("room_id")
    label = f"End your session in {room_id}?" if room_id else "End your current session?"

    return EndSessionProposal(
        session_id=session.get("id", ""),
        label=label,
    )


async def propose_room_change(
    room_name: str,
    token: str,
    client: BackendClient,
    minutes: int | None = None,
) -> RoomChangeProposal | RoomNotFoundResult:
    """
    Resolve `room_name` (case-insensitively) against currently free rooms
    and turn it into a RoomChangeProposal.

    Args:
        room_name: The room name as the user said it, e.g. "room 101".
        token: User authentication token.
        client: Backend client instance.
        minutes: Optional duration to search free rooms for. Defaults to
            DEFAULT_ROOM_SEARCH_MINUTES.

    Returns:
        A RoomChangeProposal for the matching free room, or a
        RoomNotFoundResult that points back at room search instead of
        raising when no free room matches the name.
    """
    search_minutes = minutes if minutes is not None else DEFAULT_ROOM_SEARCH_MINUTES
    rooms = await client.get_empty_rooms(token=token, minutes=search_minutes)

    target = room_name.strip().casefold()
    match = next((room for room in rooms if room.name.strip().casefold() == target), None)

    if match is None:
        return RoomNotFoundResult(
            requested_name=room_name,
            message=(
                f"I couldn't find a free room called '{room_name}'. "
                "Want me to search available rooms instead?"
            ),
        )

    return RoomChangeProposal(
        to_room_id=match.id,
        to_room_name=match.name,
        minutes=minutes,
        label=f"Move to {match.name}?",
    )
