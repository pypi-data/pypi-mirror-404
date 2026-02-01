from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import ValidationError

from utilityhub_config.metadata import SettingsMetadata


class ConfigError(Exception):
    """Base configuration error."""


@dataclass
class ConfigValidationError(ConfigError):
    message: str
    errors: ValidationError
    metadata: SettingsMetadata
    checked_files: Iterable[str]
    precedence: list[str]

    def __str__(self) -> str:  # human-friendly
        case_lines = [self.message, ""]
        case_lines.append("Validation errors:")
        case_lines.extend([str(self.errors)])
        case_lines.append("")
        case_lines.append("Files checked:")
        case_lines.extend([f" - {p}" for p in self.checked_files])
        case_lines.append("")
        case_lines.append("Precedence (low -> high):")
        case_lines.append(" -> ".join(self.precedence))
        case_lines.append("")
        case_lines.append("Field sources:")
        for k, v in self.metadata.per_field.items():
            case_lines.append(f" - {k}: {v.source} ({v.source_path})")
        return "\n".join(case_lines)
