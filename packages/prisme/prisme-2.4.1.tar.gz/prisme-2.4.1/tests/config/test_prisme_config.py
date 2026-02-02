"""Tests for PrismeConfig and TOML loader."""

import pytest

from prisme.config.loader import ConfigLoadError, load_prisme_config
from prisme.config.schema import PrismeConfig


class TestPrismeConfig:
    def test_minimal(self):
        config = PrismeConfig(prisme_version="2.0.0")
        assert config.prisme_version == "2.0.0"
        assert config.config_version == 1
        assert config.project.spec_path == "specs/models.py"
        assert config.generation.mode == "strict"
        assert config.tools.python_manager == "uv"

    def test_full(self):
        config = PrismeConfig(
            prisme_version="2.0.0",
            config_version=1,
            project={"spec_path": "specs/domain.py", "project_path": "specs/infra.py"},
            generation={"mode": "lenient", "auto_format": False},
            tools={"python_manager": "pip", "package_manager": "pnpm"},
        )
        assert config.project.spec_path == "specs/domain.py"
        assert config.generation.mode == "lenient"
        assert config.tools.package_manager == "pnpm"

    def test_forbids_extra(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PrismeConfig(prisme_version="2.0.0", unknown="bad")


class TestTOMLLoader:
    def test_load_valid(self, tmp_path):
        toml_file = tmp_path / "prisme.toml"
        toml_file.write_text(
            "[prisme]\n"
            'prisme_version = "2.0.0"\n'
            "config_version = 1\n"
            "\n"
            "[project]\n"
            'spec_path = "specs/models.py"\n'
        )
        # The TOML structure needs to match the flat model
        # PrismeConfig expects top-level keys
        toml_file.write_text(
            'prisme_version = "2.0.0"\n'
            "config_version = 1\n"
            "\n"
            "[project]\n"
            'spec_path = "specs/domain.py"\n'
        )
        config = load_prisme_config(toml_file)
        assert config.prisme_version == "2.0.0"
        assert config.project.spec_path == "specs/domain.py"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(ConfigLoadError, match="not found"):
            load_prisme_config(tmp_path / "missing.toml")

    def test_load_invalid_toml(self, tmp_path):
        toml_file = tmp_path / "prisme.toml"
        toml_file.write_text("invalid toml {{{}}")
        with pytest.raises(ConfigLoadError, match="Invalid TOML"):
            load_prisme_config(toml_file)

    def test_load_invalid_config(self, tmp_path):
        toml_file = tmp_path / "prisme.toml"
        toml_file.write_text('unknown_key = "bad"\n')
        with pytest.raises(ConfigLoadError, match="Invalid configuration"):
            load_prisme_config(toml_file)
