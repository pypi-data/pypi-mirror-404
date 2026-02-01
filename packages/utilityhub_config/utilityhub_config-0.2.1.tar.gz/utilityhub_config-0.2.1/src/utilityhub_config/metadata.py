from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldSource:
    source: str
    source_path: str | None
    raw_value: Any


@dataclass
class SettingsMetadata:
    per_field: dict[str, FieldSource]

    def get_source(self, field: str) -> FieldSource | None:
        return self.per_field.get(field)
