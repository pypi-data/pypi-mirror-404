from __future__ import annotations

from pathlib import Path


def parse_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file into a dictionary.

    Uses python-dotenv for robust parsing with support for:
    - Comments (lines starting with #)
    - Quoted values (single and double quotes)
    - Escape sequences
    - Variable expansion (if expand_vars is True)

    Args:
        path: Path to the .env file.

    Returns:
        A dictionary of environment variables from the file, or empty dict if file doesn't exist.
    """
    if not path.exists():
        return {}
    try:
        from dotenv import dotenv_values

        values = dotenv_values(path) or {}
        # Ensure all values are strings (python-dotenv can return None)
        return {k: (v or "") for k, v in values.items()}
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"dotenv file found at {path}, but python-dotenv is not installed. "
            "Install 'python-dotenv' to enable .env file support."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to parse .env file at {path}: {exc}") from exc
