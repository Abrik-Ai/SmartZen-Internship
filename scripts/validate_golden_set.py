import sys

from app.evals.load_golden_set import load_golden_set

REQUIRED_KEYS = {"category", "id", "message", "role", "expect_tool", "expect_proposal"}
ALLOWED_ROLES= {"INSTRUCTOR", "SUPER_ADMIN", "BUILDING_COORDINATOR", "FACULTY_COORDINATOR"}
ALLOWED_TOOLS = {"get_my_schedule", "find_free_rooms", "get_room_status", 
                 "documentation_search", None}
ALLOWED_PROPOSALS = (dict, type(None))
VALID_CATEGORIES = {"normal", "typo", "ambiguous", "adversarial", "no_tool"}

def validate_set(entries: list[dict]) -> list[str]:
    errors = []
    seen_ids = set()
    for entry in entries:
        entry_id = entry.get("id", 'unknown')
        if "id" in entry:
            if entry_id in seen_ids:
                errors.append(f"Duplicate ID found across golden set: '{entry_id}'")
            else:
                seen_ids.add(entry_id)

        missing_keys = REQUIRED_KEYS - entry.keys()
        if missing_keys:
            errors.append(f"Entry {entry.get('id', 'unknown')} is missing"
            f" required keys: {missing_keys}")

        if "role" in entry and entry["role"] not in ALLOWED_ROLES:
            errors.append(
                 f"Entry {entry.get('id', 'unknown')} has an invalid role: '{entry['role']}'. "
                 f"Allowed roles are: {ALLOWED_ROLES}"
            )

        if "expect_tool" in entry and entry["expect_tool"] not in ALLOWED_TOOLS:
            errors.append(
                f"Entry {entry.get('id', 'unknown')} has an invalid expected tool: "
                f"'{entry['expect_tool']}'. "
                f"Allowed tools are: {ALLOWED_TOOLS}"
            )

        if "expect_proposal" in entry and not isinstance(
            entry["expect_proposal"], ALLOWED_PROPOSALS
            ):
            errors.append(
                f"Entry {entry.get('id', 'unknown')} has an invalid expected proposal type:"
                f"{type(entry['expect_proposal'])}"
            )

        if "category" in entry and entry["category"] not in VALID_CATEGORIES:
            errors.append(
                f"Entry {entry.get('id', 'unknown')} has an invalid category: "
                f"'{entry['category']}'. "
                f"Valid categories are: {VALID_CATEGORIES}"
            )

    return errors

if __name__ == "__main__":
    golden_set = load_golden_set("../smartzen-ai/app/evals/data/golden_set.yaml")
    errors = validate_set(golden_set)
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("All entries are valid")

