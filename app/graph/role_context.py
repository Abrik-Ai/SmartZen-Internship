def get_role_context(caller: str) -> str:
    """Return plain-English context for the caller's role."""

    caller = caller.upper()

    if caller == "INSTRUCTOR":
        return "\n".join(
            [
                "The instructor is checked into ST101.",
                "Current class: Physics 101, scheduled to end at 15:00 (about 25 min left).",
                "Latest readings: temperature 24.3C, humidity 41%, CO2 620 ppm, "
                "AC off, window closed, room occupied.",
            ]
        )

    if caller in {"FACULTY_COORDINATOR", "BUILDING_COORDINATOR", "SUPER_ADMIN"}:
        return "\n".join(
            [
                "You are assisting a building coordinator overseeing building ST.",
                "Right now there are 4 active class sessions across 30 rooms, "
                "with 12 currently free.",
            ]
        )

    return ""