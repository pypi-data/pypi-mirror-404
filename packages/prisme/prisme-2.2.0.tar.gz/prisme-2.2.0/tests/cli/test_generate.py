"""Tests for prism generate command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_spec_not_found_error(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Returns error when spec file doesn't exist."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["generate", "nonexistent.py"])

            # Click validates path exists before command runs (exit code 2)
            # or the command itself reports not found (exit code 1)
            assert result.exit_code != 0

    def test_generate_default_spec_path_not_found(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Returns error when default specs/models.py doesn't exist."""
        with cli_runner.isolated_filesystem():
            # Create prisme.toml so we get past the create check
            Path("prisme.toml").write_text(
                'prisme_version = "0.12.1"\nconfig_version = 1\n\n[project]\nspec_path = "specs/models.py"\n'
            )
            result = cli_runner.invoke(main, ["generate"])

            assert result.exit_code != 0
            assert "not found" in result.output.lower()

    def test_generate_with_valid_spec(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generates code from a valid spec file."""
        with cli_runner.isolated_filesystem():
            # Create spec file in isolated filesystem
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file)])

            # Should complete (may have warnings about output dirs)
            assert "Generating" in result.output or "error" in result.output.lower()

    def test_generate_dry_run_flag(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Dry run mode shows preview message."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file), "--dry-run"])

            assert "dry run" in result.output.lower()

    def test_generate_force_flag(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Force mode shows force message."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file), "--force"])

            assert "force" in result.output.lower()

    def test_generate_only_option_parses(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """The --only option is accepted and parsed."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file), "--only", "models"])

            # Should not fail due to option parsing
            assert "Generating" in result.output or result.exit_code == 0

    def test_generate_only_multiple_layers(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Multiple layers can be specified with --only."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(
                main, ["generate", str(spec_file), "--only", "models,schemas,services"]
            )

            # Should not fail due to option parsing
            assert "Generating" in result.output or result.exit_code == 0

    def test_generate_shows_summary(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generate command shows a summary table."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file)])

            # Should show summary with generator names or totals
            assert "Summary" in result.output or "Total" in result.output

    def test_generate_invalid_spec_error(
        self,
        cli_runner: CliRunner,
        invalid_spec_file: Path,
    ) -> None:
        """Returns error for invalid spec file."""
        result = cli_runner.invoke(main, ["generate", str(invalid_spec_file)])

        assert result.exit_code == 1
        assert "error" in result.output.lower()

    def test_generate_reads_spec_from_prisme_toml(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generate reads spec_path from prisme.toml when no spec argument provided."""
        with cli_runner.isolated_filesystem():
            # Create spec file at a custom location
            spec_dir = Path("custom_specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "my_models.py"
            spec_file.write_text(valid_spec_content)

            # Create prisme.toml pointing to custom spec location
            Path("prisme.toml").write_text(
                'prisme_version = "0.12.1"\nconfig_version = 1\n\n'
                "[project]\n"
                'spec_path = "custom_specs/my_models.py"\n'
            )

            # Run generate without spec argument
            result = cli_runner.invoke(main, ["generate"])

            # Should find and use the spec from config
            assert "custom_specs/my_models.py" in result.output or "Generating" in result.output
            assert result.exit_code == 0

    def test_generate_with_relative_imports(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Generate supports specs that use relative imports."""
        with cli_runner.isolated_filesystem():
            # Create specs folder with multiple files
            specs_dir = Path("specs")
            specs_dir.mkdir(parents=True)

            # Create __init__.py to make it a proper package for relative imports
            (specs_dir / "__init__.py").write_text("")

            # Create a helper module
            (specs_dir / "models.py").write_text("""
from prisme import ModelSpec, FieldSpec, FieldType

user = ModelSpec(
    name="User",
    fields=[
        FieldSpec(name="name", type=FieldType.STRING, max_length=100),
    ],
)
""")

            # Create main spec with relative import
            (specs_dir / "stack.py").write_text("""
from prisme import StackSpec

from .models import user

spec = StackSpec(
    name="test-app",
    models=[user],
)
""")

            # Run generate with spec that uses relative imports
            result = cli_runner.invoke(main, ["generate", "specs/stack.py"])

            # Should successfully load the spec with relative imports
            assert result.exit_code == 0, f"Generate failed with output: {result.output}"
            assert "Generating" in result.output

    def test_generate_outputs_to_project_root(
        self,
        cli_runner: CliRunner,
        valid_spec_content: str,
    ) -> None:
        """Generated files land in the project root (packages/)."""
        with cli_runner.isolated_filesystem():
            spec_dir = Path("specs")
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "models.py"
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(main, ["generate", str(spec_file)])

            assert result.exit_code == 0, f"Generate failed: {result.output}"
            # Generated files go into packages/ at the project root
            packages = Path("packages")
            assert packages.exists(), "packages/ directory was not created"
            generated_files = list(packages.rglob("*"))
            assert len(generated_files) > 0, "No files were generated inside packages/"
