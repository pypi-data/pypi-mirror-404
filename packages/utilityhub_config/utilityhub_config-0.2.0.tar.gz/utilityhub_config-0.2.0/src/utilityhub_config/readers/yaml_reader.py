from __future__ import annotations

from pathlib import Path
from typing import Any


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml

        with path.open("r", encoding="utf8") as fh:
            return yaml.safe_load(fh) or {}
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"YAML file found at {path}, but PyYAML is not installed. Install 'PyYAML' to enable YAML support."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to parse YAML at {path}: {exc}") from exc
