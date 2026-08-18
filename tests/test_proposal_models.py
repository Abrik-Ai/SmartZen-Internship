from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.proposals import (
    ControlProposal,
    EndSessionProposal,
    ExtendProposal,
    RoomChangeProposal,
)

# ---------------------------------------------------------------------------
# ControlProposal
# ---------------------------------------------------------------------------


def test_control_proposal_kind_defaults_without_being_passed() -> None:
    proposal = ControlProposal(room_id="r1", device="lights", on=True, label="Turn on lights?")

    assert proposal.kind == "control"


def test_control_proposal_kind_can_be_passed_explicitly_if_correct() -> None:
    proposal = ControlProposal(
        kind="control", room_id="r1", device="lights", on=True, label="Turn on lights?"
    )

    assert proposal.kind == "control"


def test_control_proposal_rejects_mismatched_kind() -> None:
    with pytest.raises(ValidationError):
        ControlProposal(
            kind="extend",  # type: ignore[arg-type]
            room_id="r1",
            device="lights",
            on=True,
            label="Turn on lights?",
        )


@pytest.mark.parametrize("missing_field", ["room_id", "device", "on", "label"])
def test_control_proposal_requires_all_non_kind_fields(missing_field: str) -> None:
    fields = {"room_id": "r1", "device": "lights", "on": True, "label": "Turn on lights?"}
    del fields[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        ControlProposal(**fields)  # type: ignore[arg-type]

    assert any(err["loc"] == (missing_field,) for err in exc_info.value.errors())


# ---------------------------------------------------------------------------
# ExtendProposal
# ---------------------------------------------------------------------------


def test_extend_proposal_kind_defaults_without_being_passed() -> None:
    proposal = ExtendProposal(
        session_id="sess-1", until="2026-08-11T12:30:00Z", label="Extend by 20 minutes?"  # type: ignore[arg-type]
    )

    assert proposal.kind == "extend"


def test_extend_proposal_rejects_mismatched_kind() -> None:
    with pytest.raises(ValidationError):
        ExtendProposal(
            kind="control",  # type: ignore[arg-type]
            session_id="sess-1",
            until="2026-08-11T12:30:00Z",  # type: ignore[arg-type]
            label="Extend by 20 minutes?",
        )


@pytest.mark.parametrize("missing_field", ["session_id", "until", "label"])
def test_extend_proposal_requires_all_non_kind_fields(missing_field: str) -> None:
    fields = {
        "session_id": "sess-1",
        "until": "2026-08-11T12:30:00Z",
        "label": "Extend by 20 minutes?",
    }
    del fields[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        ExtendProposal(**fields)  # type: ignore[arg-type]

    assert any(err["loc"] == (missing_field,) for err in exc_info.value.errors())


def test_extend_proposal_parses_iso_datetime_string_into_datetime() -> None:
    proposal = ExtendProposal(
        session_id="sess-1",
        until="2026-08-11T12:30:00Z",  # type: ignore[arg-type]
        label="Extend by 20 minutes?",
    )

    assert isinstance(proposal.until, datetime)
    assert proposal.until.year == 2026
    assert proposal.until.month == 8
    assert proposal.until.day == 11
    assert proposal.until.hour == 12
    assert proposal.until.minute == 30


def test_extend_proposal_accepts_a_real_datetime_object_directly() -> None:
    until = datetime(2026, 8, 11, 12, 30, 0)
    proposal = ExtendProposal(session_id="sess-1", until=until, label="Extend by 20 minutes?")

    assert proposal.until == until


def test_extend_proposal_rejects_a_non_date_string() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ExtendProposal(
            session_id="sess-1",
            until="not a date at all",  # type: ignore[arg-type]
            label="Extend by 20 minutes?",
        )

    assert any(err["loc"] == ("until",) for err in exc_info.value.errors())


# ---------------------------------------------------------------------------
# EndSessionProposal
# ---------------------------------------------------------------------------


def test_end_session_proposal_kind_defaults_without_being_passed() -> None:
    proposal = EndSessionProposal(session_id="sess-1", label="End your session?")

    assert proposal.kind == "end_session"


def test_end_session_proposal_rejects_mismatched_kind() -> None:
    with pytest.raises(ValidationError):
        EndSessionProposal(
            kind="control",  # type: ignore[arg-type]
            session_id="sess-1",
            label="End your session?",
        )


@pytest.mark.parametrize("missing_field", ["session_id", "label"])
def test_end_session_proposal_requires_all_non_kind_fields(missing_field: str) -> None:
    fields = {"session_id": "sess-1", "label": "End your session?"}
    del fields[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        EndSessionProposal(**fields)  # type: ignore[arg-type]

    assert any(err["loc"] == (missing_field,) for err in exc_info.value.errors())


# ---------------------------------------------------------------------------
# RoomChangeProposal
# ---------------------------------------------------------------------------


def test_room_change_proposal_kind_defaults_without_being_passed() -> None:
    proposal = RoomChangeProposal(to_room_id="r2", to_room_name="Room 202", label="Move rooms?")

    assert proposal.kind == "room_change"


def test_room_change_proposal_rejects_mismatched_kind() -> None:
    with pytest.raises(ValidationError):
        RoomChangeProposal(
            kind="extend",  # type: ignore[arg-type]
            to_room_id="r2",
            to_room_name="Room 202",
            label="Move rooms?",
        )


@pytest.mark.parametrize("missing_field", ["to_room_id", "to_room_name", "label"])
def test_room_change_proposal_requires_its_non_optional_fields(missing_field: str) -> None:
    fields = {"to_room_id": "r2", "to_room_name": "Room 202", "label": "Move rooms?"}
    del fields[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        RoomChangeProposal(**fields)  # type: ignore[arg-type]

    assert any(err["loc"] == (missing_field,) for err in exc_info.value.errors())


def test_room_change_proposal_optional_fields_default_to_none() -> None:
    proposal = RoomChangeProposal(to_room_id="r2", to_room_name="Room 202", label="Move rooms?")

    assert proposal.minutes is None
    assert proposal.note is None


def test_room_change_proposal_optional_fields_can_be_set() -> None:
    proposal = RoomChangeProposal(
        to_room_id="r2",
        to_room_name="Room 202",
        minutes=30,
        note="closer to the lift",
        label="Move rooms?",
    )

    assert proposal.minutes == 30
    assert proposal.note == "closer to the lift"
