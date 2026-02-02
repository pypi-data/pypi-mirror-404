"""Tests for config includes (prisme.d/*.toml)."""

from pathlib import Path

from prisme.config.loader import ConfigLoadError, _deep_merge, load_prisme_config


def test_deep_merge_basic() -> None:
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99, "e": 5}, "f": 6}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": {"c": 99, "d": 3, "e": 5}, "f": 6}


def test_deep_merge_no_mutation() -> None:
    base = {"a": {"b": 1}}
    override = {"a": {"c": 2}}
    _deep_merge(base, override)
    assert base == {"a": {"b": 1}}


def test_load_without_includes(tmp_path: Path) -> None:
    toml = tmp_path / "prisme.toml"
    toml.write_text('prisme_version = "2.0.0"\nconfig_version = 1\n')
    config = load_prisme_config(toml)
    assert config.prisme_version == "2.0.0"


def test_load_with_includes(tmp_path: Path) -> None:
    toml = tmp_path / "prisme.toml"
    toml.write_text('prisme_version = "2.0.0"\nconfig_version = 1\n')

    include_dir = tmp_path / "prisme.d"
    include_dir.mkdir()
    (include_dir / "tools.toml").write_text('[tools]\npython_manager = "poetry"\n')

    config = load_prisme_config(toml)
    assert config.tools.python_manager == "poetry"


def test_load_includes_sorted_order(tmp_path: Path) -> None:
    toml = tmp_path / "prisme.toml"
    toml.write_text('prisme_version = "2.0.0"\nconfig_version = 1\n')

    include_dir = tmp_path / "prisme.d"
    include_dir.mkdir()
    (include_dir / "01-base.toml").write_text('[tools]\npython_manager = "pip"\n')
    (include_dir / "02-override.toml").write_text('[tools]\npython_manager = "uv"\n')

    config = load_prisme_config(toml)
    assert config.tools.python_manager == "uv"


def test_load_includes_invalid_toml(tmp_path: Path) -> None:
    toml = tmp_path / "prisme.toml"
    toml.write_text('prisme_version = "2.0.0"\nconfig_version = 1\n')

    include_dir = tmp_path / "prisme.d"
    include_dir.mkdir()
    (include_dir / "bad.toml").write_text("this is not valid toml {{{}}")

    try:
        load_prisme_config(toml)
        raise AssertionError("Should have raised")
    except ConfigLoadError as e:
        assert "Invalid TOML" in str(e)
