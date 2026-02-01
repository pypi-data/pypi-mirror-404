"""TOML configuration loader for prisme.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

from prisme.config.schema import PrismeConfig


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded."""


def load_prisme_config(path: Path | str) -> PrismeConfig:
    """Load PrismeConfig from a prisme.toml file.

    Args:
        path: Path to the prisme.toml file.

    Returns:
        The loaded PrismeConfig.

    Raises:
        ConfigLoadError: If the file cannot be loaded or is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise ConfigLoadError(f"Configuration file not found: {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigLoadError(f"Invalid TOML in {path}: {e}") from e

    try:
        return PrismeConfig.model_validate(data)
    except Exception as e:
        raise ConfigLoadError(f"Invalid configuration in {path}: {e}") from e


__all__ = [
    "ConfigLoadError",
    "load_prisme_config",
]
