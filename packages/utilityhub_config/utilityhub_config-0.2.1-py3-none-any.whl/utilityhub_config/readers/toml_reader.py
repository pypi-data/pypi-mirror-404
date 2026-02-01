from __future__ import annotations

from pathlib import Path
from typing import Any


def read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file and return mapping, or empty dict if not found."""
    if not path.exists():
        return {}
    try:
        import tomllib

        with path.open("rb") as fh:
            return tomllib.load(fh) or {}
    except Exception as exc:  # be explicit in errors upstream
        raise RuntimeError(f"Failed to parse TOML at {path}: {exc}") from exc
