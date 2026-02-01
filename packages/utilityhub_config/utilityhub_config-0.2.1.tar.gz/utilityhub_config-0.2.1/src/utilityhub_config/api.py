from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from utilityhub_config.errors import ConfigValidationError
from utilityhub_config.metadata import SettingsMetadata
from utilityhub_config.resolver import PrecedenceResolver

T = TypeVar("T", bound=BaseModel)


def load_settings[T: BaseModel](
    model: type[T],
    *,
    app_name: str | None = None,
    cwd: Path | None = None,
    env_prefix: str | None = None,
    config_file: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[T, SettingsMetadata]:
    """Load and validate settings for the given Pydantic model.

    Resolves configuration from multiple sources in precedence order:
    defaults → global config → [explicit file OR project config] → dotenv → environment variables → runtime overrides.

    Args:
        model: A Pydantic BaseModel subclass to validate and populate.
        app_name: Application name for config file lookup (defaults to model class name).
        cwd: Working directory for config file search (defaults to current directory).
        env_prefix: Optional prefix for environment variable lookup (e.g., 'MYAPP_').
        config_file: Explicit config file path to load as project config. If provided, skips auto-discovery
                    of {app_name}.yaml/.toml in standard locations and loads this file instead. File format
                    is auto-detected from extension (.yaml, .yml, or .toml). Still respects precedence order -
                    environment variables and overrides can override values from this file. Must exist and be
                    readable. (Optional)
        overrides: Runtime overrides as a dictionary (highest precedence).

    Returns:
        A tuple of (settings_instance, metadata) where settings_instance is an instance
        of the provided model type, and metadata tracks which source provided each field.

    Raises:
        ConfigValidationError: If validation fails, with detailed context about sources and files checked.
        ConfigError: If config_file is provided but doesn't exist, is not a file, or has an unsupported format.
    """
    cwd = Path.cwd() if cwd is None else cwd
    if config_file is not None:
        config_file = config_file.resolve()

    resolver = PrecedenceResolver(app_name=app_name, cwd=cwd, env_prefix=env_prefix, config_file=config_file)

    merged, metadata, checked_files = resolver.resolve(model=model, overrides=overrides or {})

    try:
        instance = model.model_validate(merged)
    except ValidationError as exc:  # pydantic v2
        raise ConfigValidationError(
            "Validation failed",
            errors=exc,
            metadata=metadata,
            checked_files=checked_files,
            precedence=resolver.precedence_order,
        ) from exc

    return instance, metadata
