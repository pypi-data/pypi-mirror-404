"""Tests for migration version detection."""

from pathlib import Path

from prisme.migration.detector import VersionInfo, detect_versions


def test_detect_empty_dir(tmp_path: Path) -> None:
    info = detect_versions(tmp_path)
    assert not info.has_prisme_toml
    assert not info.has_legacy_config
    assert not info.has_domain_spec
    assert not info.needs_config_migration
    assert not info.needs_domain_migration


def test_detect_v2_project(tmp_path: Path) -> None:
    (tmp_path / "prisme.toml").write_text('prisme_version = "2.0.0"\nconfig_version = 1\n')
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "models.py").write_text("PRISME_DOMAIN_VERSION = 2\n")
    (tmp_path / "specs" / "project.py").write_text("project = None\n")

    info = detect_versions(tmp_path)
    assert info.has_prisme_toml
    assert info.config_version == 1
    assert info.has_domain_spec
    assert info.domain_version == 2
    assert info.has_project_spec
    assert not info.needs_domain_migration
    assert not info.needs_project_extraction


def test_detect_v1_project(tmp_path: Path) -> None:
    (tmp_path / "prism.config.py").write_text("config = {}\n")
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "models.py").write_text("stack = StackSpec(name='test')\n")

    info = detect_versions(tmp_path)
    assert info.has_legacy_config
    assert not info.has_prisme_toml
    assert info.needs_config_migration
    assert info.domain_version == 1
    assert info.needs_domain_migration
    assert info.needs_project_extraction


def test_detect_python_manager(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_text("")
    info = detect_versions(tmp_path)
    assert info.python_manager == "uv"


def test_version_info_defaults() -> None:
    info = VersionInfo()
    assert not info.needs_config_migration
    assert not info.needs_domain_migration
    assert not info.needs_project_extraction
