from typing import Any


async def schedule_lookup_stub(range_value: str) -> list[dict[str, Any]]:
    """Return canned schedule data for graph development and testing."""

    schedules = {
        "today": [
            {
                "id": "stub-1",
                "course_label": "Physics 101",
                "start_time": "14:00",
                "end_time": "15:00",
                "room": {
                    "id": "ST101",
                    "name": "ST101",
                    "building": "ST",
                },
            },
        ],
        "week": [
            {
                "id": "stub-1",
                "course_label": "Physics 101",
                "start_time": "14:00",
                "end_time": "15:00",
                "room": {
                    "id": "ST101",
                    "name": "ST101",
                    "building": "ST",
                },
            },
            {
                "id": "stub-2",
                "course_label": "Algorithms",
                "start_time": "10:00",
                "end_time": "11:00",
                "room": {
                    "id": "ST102",
                    "name": "ST102",
                    "building": "ST",
                },
            },
        ],
        "upcoming": [
            {
                "id": "stub-1",
                "course_label": "Physics 101",
                "start_time": "14:00",
                "end_time": "15:00",
                "room": {
                    "id": "ST101",
                    "name": "ST101",
                    "building": "ST",
                },
            },
        ],
    }

    return schedules.get(range_value, [])