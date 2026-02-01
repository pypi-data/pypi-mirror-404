"""utilityhub_config

Small, deterministic configuration loader for automation tools.
"""

from utilityhub_config.api import load_settings

__all__: list[str] = ["load_settings"]


def main() -> None:
    print("utilityhub-config: use `load_settings()` in your code")
