import yaml


def load_golden_set(path: str) -> list[dict]:
    try:
        with open(path) as f:
            golden_set = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in '{path}': {e}") from e
    
    if golden_set is None:
       raise ValueError(f"File '{path}' is empty.")
    
    if not isinstance(golden_set, list):
        raise ValueError(f"Golden set in '{path}' must be a list of examples.")
    
    for example in golden_set:
        if not isinstance(example, dict):
            raise ValueError(f"Each example in '{path}' must be a dictionary.")

    return golden_set