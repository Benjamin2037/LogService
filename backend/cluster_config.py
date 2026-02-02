import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


class ConfigValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load_cluster_config(config_path: Path, schema_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = []
        for err in errors:
            path = "/".join(str(p) for p in err.path)
            loc = f"{path}: " if path else ""
            messages.append(f"{loc}{err.message}")
        raise ConfigValidationError(messages)

    return data
