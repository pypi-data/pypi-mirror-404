"""Tests for prism schema command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestSchemaCommand:
    """Tests for the schema command."""

    def test_schema_outputs_to_stdout(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Without --output, prints SDL to console."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["schema", str(spec_file)])

            assert result.exit_code == 0
            # Should contain GraphQL type definitions
            assert "type" in result.output

    def test_schema_writes_to_file(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """--output writes SDL to file."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(
                main, ["schema", str(spec_file), "--output", "schema.graphql"]
            )

            assert result.exit_code == 0
            assert Path("schema.graphql").exists()

    def test_schema_includes_model_types(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generated SDL includes model types."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["schema", str(spec_file)])

            assert "UserType" in result.output
            assert "PostType" in result.output

    def test_schema_includes_fields(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generated SDL includes model fields."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["schema", str(spec_file)])

            assert "name" in result.output
            assert "email" in result.output
            assert "title" in result.output

    def test_schema_spec_not_found(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Returns error when spec file doesn't exist."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["schema", "nonexistent.py"])

            assert result.exit_code != 0

    def test_schema_invalid_spec(
        self,
        cli_runner: CliRunner,
        invalid_spec_file: Path,
    ) -> None:
        """Returns error for invalid spec file."""
        result = cli_runner.invoke(main, ["schema", str(invalid_spec_file)])

        assert result.exit_code == 1

    def test_schema_default_spec_path(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Uses default specs/models.py when no path given."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["schema"])

            assert result.exit_code == 0
            assert "type" in result.output

    def test_schema_respects_graphql_disabled(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Skips models with graphql.enabled=False."""
        spec_content = '''"""Test specification."""
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.stack import StackSpec

stack = StackSpec(
    name="test-project",
    models=[
        ModelSpec(
            name="PublicModel",
            fields=[FieldSpec(name="name", type=FieldType.STRING)],
            expose=True,
        ),
        ModelSpec(
            name="PrivateModel",
            fields=[FieldSpec(name="secret", type=FieldType.STRING)],
            expose=False,
        ),
    ],
)
'''
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir()
            spec_file = spec_dir / "models.py"
            spec_file.write_text(spec_content)

            result = cli_runner.invoke(main, ["schema", str(spec_file)])

            assert "PublicModelType" in result.output
            assert "PrivateModelType" not in result.output
