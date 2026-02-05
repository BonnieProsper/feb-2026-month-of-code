import json
from typing import Dict, Any


def load_schema(path: str) -> Dict[str, Any]:
    """
    Load and validate a schema configuration file.

    This file defines expectations, not enforcement logic.
    Invalid configs should fail fast and loudly.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as exc:
        raise RuntimeError(f"Failed to load schema config: {exc}") from exc

    _validate_schema(config)
    return config


def _validate_schema(config: Dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ValueError("Schema config must be a JSON object")

    if "required_columns" in config:
        if not isinstance(config["required_columns"], list):
            raise ValueError("required_columns must be a list")

    if "numeric_ranges" in config:
        if not isinstance(config["numeric_ranges"], dict):
            raise ValueError("numeric_ranges must be an object")

        for col, bounds in config["numeric_ranges"].items():
            if not isinstance(bounds, dict):
                raise ValueError(f"Range for {col} must be an object")
            if "min" not in bounds or "max" not in bounds:
                raise ValueError(f"Range for {col} must define min and max")

    if "severity" in config:
        if not isinstance(config["severity"], dict):
            raise ValueError("severity must be an object mapping check_name -> level")
        for k, v in config["severity"].items():
            if v not in {"pass", "warn", "fail"}:
                raise ValueError(f"Invalid severity '{v}' for check '{k}'")

    if "ignore_columns" in config:
        if not isinstance(config["ignore_columns"], list):
            raise ValueError("ignore_columns must be a list")

    if "ignore" in config:
        if not isinstance(config["ignore"], dict):
            raise ValueError("ignore must be an object mapping check_name -> column list")
