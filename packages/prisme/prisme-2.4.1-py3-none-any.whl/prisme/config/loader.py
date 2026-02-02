"""TOML configuration loader for prisme.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from prisme.config.schema import PrismeConfig


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge override into base, returning a new dict.

    For nested dicts, merges recursively. For other values, override wins.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_includes(config_dir: Path) -> dict[str, Any]:
    """Load and merge all TOML files from prisme.d/ directory.

    Files are loaded in sorted order so behavior is deterministic.

    Args:
        config_dir: Directory containing the main prisme.toml.

    Returns:
        Merged dict from all include files, or empty dict if none.
    """
    include_dir = config_dir / "prisme.d"
    if not include_dir.is_dir():
        return {}

    merged: dict[str, Any] = {}
    for toml_file in sorted(include_dir.glob("*.toml")):
        try:
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
            merged = _deep_merge(merged, data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigLoadError(f"Invalid TOML in {toml_file}: {e}") from e

    return merged


def load_prisme_config(path: Path | str) -> PrismeConfig:
    """Load PrismeConfig from a prisme.toml file.

    Also merges any TOML files found in a sibling ``prisme.d/`` directory.
    Files in ``prisme.d/`` are loaded in sorted order and deep-merged on top
    of the main config.

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

    # Merge includes from prisme.d/
    includes = _load_includes(path.parent)
    if includes:
        data = _deep_merge(data, includes)

    try:
        return PrismeConfig.model_validate(data)
    except Exception as e:
        raise ConfigLoadError(f"Invalid configuration in {path}: {e}") from e


__all__ = [
    "ConfigLoadError",
    "load_prisme_config",
]
