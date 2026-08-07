def load_golden_set(path: str) -> list[dict]:
    try:
        with open(path, 'r') as f:
            golden_set = yaml.safe_load(f)
            return golden_set
    except FileNotFoundError:
        raise FileNotFoundError("Golden set file not found")

    