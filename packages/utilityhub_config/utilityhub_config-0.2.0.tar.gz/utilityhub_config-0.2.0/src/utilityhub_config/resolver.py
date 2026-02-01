from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from utilityhub_config.errors import ConfigError
from utilityhub_config.metadata import FieldSource, SettingsMetadata
from utilityhub_config.readers import parse_dotenv, read_toml, read_yaml


@dataclass
class PrecedenceResolver:
    """Resolves configuration from multiple sources in precedence order.

    Attributes:
        app_name: Application name for config file lookup. If None, derived from model class name.
        cwd: Working directory for config file search (defaults: current working directory).
        env_prefix: Optional prefix for environment variable lookup (e.g., 'MYAPP_').
        config_file: Explicit config file path to load as project config. If provided, skips auto-discovery.
    """

    app_name: str | None = None
    cwd: Path = field(default_factory=Path.cwd)
    env_prefix: str | None = None
    config_file: Path | None = None

    def __post_init__(self) -> None:
        if self.cwd is None:
            self.cwd = Path.cwd()
        self.precedence_order = [
            "defaults",
            "global",
            "project",
            "dotenv",
            "env",
            "overrides",
        ]

    def resolve(
        self, *, model: type[BaseModel], overrides: dict[str, Any]
    ) -> tuple[dict[str, Any], SettingsMetadata, list[str]]:
        app = self._determine_app_name(model)

        checked_files: list[str] = []
        per_field: dict[str, FieldSource] = {}

        # 1. defaults from model
        merged: dict[str, Any] = {}
        defaults = self._model_defaults(model)
        merged.update(defaults)
        for k, v in defaults.items():
            per_field[k] = FieldSource("defaults", None, v)

        # 2. global config
        global_paths = self._global_config_paths(app)
        for p in global_paths:
            checked_files.append(str(p))
            if p.exists():
                data = read_toml(p) if p.suffix.lower() == ".toml" else read_yaml(p)
                self._merge_into(merged, per_field, data, source_name="global", source_path=str(p))

        # 3. project config (explicit file or auto-discovery)
        if self.config_file is not None:
            # Explicit config_file provided: validate and load it
            checked_files.append(str(self.config_file))
            if not self.config_file.exists():
                raise ConfigError(f"Config file not found: {self.config_file}")
            if not self.config_file.is_file():
                raise ConfigError(f"Config file path is not a file: {self.config_file}")

            # Detect format from file extension
            suffix = self.config_file.suffix.lower()
            if suffix in {".yaml", ".yml"}:
                data = read_yaml(self.config_file)
            elif suffix == ".toml":
                data = read_toml(self.config_file)
            else:
                raise ConfigError(f"Unsupported config file format: {suffix}. Supported formats: .yaml, .yml, .toml")

            self._merge_into(merged, per_field, data, source_name="project", source_path=str(self.config_file))
        else:
            # No explicit file: use auto-discovery
            project_files = self._project_config_paths(app)
            for p in project_files:
                checked_files.append(str(p))
                if p.exists():
                    data = read_toml(p) if p.suffix.lower() == ".toml" else read_yaml(p)
                    self._merge_into(merged, per_field, data, source_name="project", source_path=str(p))

        # 4. dotenv
        dotenv_path = self.cwd / ".env"
        checked_files.append(str(dotenv_path))
        dotenv_data = parse_dotenv(dotenv_path)
        # dotenv keys are usually uppercase; normalize to field names
        normalized_dotenv = {self._normalize(k): v for k, v in dotenv_data.items()}
        self._merge_into(merged, per_field, normalized_dotenv, source_name="dotenv", source_path=str(dotenv_path))

        # 5. environment variables
        env_map: dict[str, Any] = {}
        for field_name in self._field_names(model):
            candidates: list[str] = []
            if self.env_prefix:
                candidates.append(f"{self.env_prefix}_{field_name.upper()}")
            candidates.append(field_name.upper())
            for name in candidates:
                if name in os.environ:
                    env_map[field_name] = os.environ[name]
                    per_field[field_name] = FieldSource("env", f"ENV:{name}", os.environ[name])
                    break

        merged.update(env_map)

        # 6. overrides
        if overrides:
            self._merge_into(merged, per_field, overrides, source_name="overrides", source_path="runtime")

        metadata = SettingsMetadata(per_field=per_field)
        return merged, metadata, checked_files

    def _model_defaults(self, model: type[BaseModel]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        # pydantic v2
        fields = getattr(model, "model_fields", None)
        if fields is not None:
            for k, info in fields.items():
                if getattr(info, "default", None) not in (None, ...):
                    out[k] = info.default
        else:
            # pydantic v1 style
            fields = getattr(model, "__fields__", {})
            for k, f in fields.items():
                if f.default is not None:
                    out[k] = f.default
        return out

    def _field_names(self, model: type[BaseModel]) -> list[str]:
        fields = getattr(model, "model_fields", None)
        if fields is not None:
            return list(fields.keys())
        return list(getattr(model, "__fields__", {}).keys())

    def _determine_app_name(self, model: type[BaseModel]) -> str:
        """Determine the app name from explicit arg, model default, or class name.

        Precedence: explicit app_name > model field default > model class name (lowercased).
        """
        if self.app_name:
            return self.app_name
        # try to pull default from model field 'app_name' if present
        fields = getattr(model, "model_fields", None)
        if fields and "app_name" in fields:
            default = fields["app_name"].default
            if default not in (None, ...):
                return str(default)
        # fallback to model class name
        return model.__name__.lower()

    def _global_config_paths(self, app: str) -> list[Path]:
        home = Path.home()
        cfg_dir = home / ".config" / app
        return [cfg_dir / f"{app}.toml", cfg_dir / f"{app}.yaml"]

    def _project_config_paths(self, app: str) -> list[Path]:
        out: list[Path] = []
        root_toml = self.cwd / f"{app}.toml"
        root_yaml = self.cwd / f"{app}.yaml"
        out.extend([root_toml, root_yaml])
        config_dir = self.cwd / "config"
        if config_dir.exists() and config_dir.is_dir():
            for ext in ("*.toml", "*.yaml", "*.yml"):
                out.extend(sorted(config_dir.glob(ext)))
        return out

    def _normalize(self, key: str) -> str:
        return key.strip().lower().replace("-", "_")

    def _merge_into(
        self,
        target: dict[str, Any],
        per_field: dict[str, FieldSource],
        source: dict[str, Any],
        *,
        source_name: str,
        source_path: str | None = None,
    ) -> None:
        # source keys may be in various forms; normalize and map to fields
        for k, v in source.items():
            nk = self._normalize(str(k))
            # if key is nested mapping matching field exactly, allow
            target[nk] = v
            per_field[nk] = FieldSource(source_name, source_path, v)
