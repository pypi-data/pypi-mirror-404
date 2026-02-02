"""Tests for prism create command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from prisme.cli import main

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from click.testing import CliRunner


class TestCreateCommand:
    """Tests for the create command."""

    def test_create_project_creates_directory(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create command creates the project directory."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(
                main,
                ["create", "my-test-project", "--no-install", "--no-git", "-y"],
            )

            project_dir = Path("my-test-project")
            assert project_dir.exists()
            assert project_dir.is_dir()

    def test_create_shows_success_message(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create command shows success message on completion."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                ["create", "my-project", "--no-install", "--no-git", "-y"],
            )

            assert result.exit_code == 0
            assert "success" in result.output.lower()

    def test_create_shows_next_steps(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create command shows next steps after creation."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                ["create", "my-project", "--no-install", "--no-git", "-y"],
            )

            assert "cd my-project" in result.output
            assert "prisme generate" in result.output or "prisme dev" in result.output

    def test_create_minimal_template(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with minimal template succeeds."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "minimal-project",
                    "--template",
                    "minimal",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            assert Path("minimal-project").exists()

    def test_create_full_template(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with full template succeeds."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "full-project",
                    "--template",
                    "full",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            assert Path("full-project").exists()

    def test_create_api_only_template(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with api-only template succeeds."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "api-project",
                    "--template",
                    "api-only",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            assert Path("api-project").exists()

    @pytest.mark.skip(reason="saas template not yet implemented")
    def test_create_saas_template(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with saas template succeeds."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "saas-project",
                    "--template",
                    "saas",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            assert Path("saas-project").exists()

    @pytest.mark.parametrize(
        "template,project_name,ext_subdir",
        [
            ("minimal", "ext-minimal", "src/ext_minimal/extensions"),
            ("full", "ext-full", "packages/backend/src/ext_full/extensions"),
            ("api-only", "ext-api-only", "src/ext_api_only/extensions"),
        ],
    )
    def test_create_scaffolds_extension_stubs(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
        template: str,
        project_name: str,
        ext_subdir: str,
    ) -> None:
        """Create scaffolds extension stubs in the correct location for all templates."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    project_name,
                    "--template",
                    template,
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            ext_dir = Path(project_name) / ext_subdir
            assert ext_dir.is_dir()
            for filename in [
                "__init__.py",
                "dependencies.py",
                "routers.py",
                "events.py",
                "policies.py",
            ]:
                assert (ext_dir / filename).exists(), f"Missing {filename}"

    def test_create_invalid_template_fails(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with unknown template fails."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "bad-project",
                    "--template",
                    "nonexistent",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            # Click validates choice options before command runs
            assert result.exit_code != 0

    def test_create_with_sqlite_database(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with SQLite database option."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "sqlite-project",
                    "--database",
                    "sqlite",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

    def test_create_with_postgresql_database(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with PostgreSQL database option."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "pg-project",
                    "--database",
                    "postgresql",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

    def test_create_with_npm_package_manager(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with npm package manager option."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "npm-project",
                    "--package-manager",
                    "npm",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

    def test_create_with_uv_python_manager(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with uv python manager option."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "uv-project",
                    "--python-manager",
                    "uv",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

    def test_create_no_git_skips_init(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """--no-git flag prevents git initialization."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(
                main,
                ["create", "no-git-project", "--no-install", "--no-git", "-y"],
            )

            # Git init should not have been called
            git_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "git" in str(call) and "init" in str(call)
            ]
            assert len(git_calls) == 0

    def test_create_existing_directory_prompts(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create prompts when directory exists (without -y)."""
        with cli_runner.isolated_filesystem():
            # Create existing directory
            Path("existing-project").mkdir()

            # Without -y, should prompt (we simulate 'n' response)
            result = cli_runner.invoke(
                main,
                ["create", "existing-project", "--no-install", "--no-git"],
                input="n\n",
            )

            assert "Aborted" in result.output or result.exit_code == 0

    def test_create_with_spec_file(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
        valid_spec_content: str,
    ) -> None:
        """Create with --spec stores spec path reference in prisme.toml."""
        with cli_runner.isolated_filesystem():
            # Create a spec file inside the project directory first
            project_dir = Path("spec-project")
            project_dir.mkdir(parents=True)
            spec_file = project_dir / "specs" / "my-spec.py"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "spec-project",
                    "--spec",
                    str(spec_file),
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0
            # prisme.toml should contain reference to spec file
            config_file = Path("spec-project/prisme.toml")
            assert config_file.exists()
            config_content = config_file.read_text()
            assert "specs/my-spec.py" in config_content or "my-spec.py" in config_content

    def test_create_with_spec_outside_project_fails(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
        valid_spec_content: str,
    ) -> None:
        """Create with --spec fails if spec is outside project folder."""
        with cli_runner.isolated_filesystem():
            # Create a spec file outside the project directory
            spec_file = Path("external-spec.py")
            spec_file.write_text(valid_spec_content)

            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "my-project",
                    "--spec",
                    str(spec_file),
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code != 0
            assert "must be within the project folder" in result.output

    def test_create_full_template_calls_vite_scaffold(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with full template attempts to scaffold frontend with Vite."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "vite-project",
                    "--template",
                    "full",
                    "--package-manager",
                    "pnpm",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Verify create-vite was called
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) > 0

    def test_create_minimal_template_skips_vite_scaffold(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with minimal template does not call Vite scaffold."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "minimal-project",
                    "--template",
                    "minimal",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Verify create-vite was NOT called
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) == 0

    def test_create_api_only_template_skips_vite_scaffold(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with api-only template does not call Vite scaffold."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "api-project",
                    "--template",
                    "api-only",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Verify create-vite was NOT called
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) == 0

    def test_create_full_template_with_npm(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with full template uses correct npm command for Vite."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "npm-vite-project",
                    "--template",
                    "full",
                    "--package-manager",
                    "npm",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Find the create-vite call and verify it uses npm syntax
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "npm" in str(call) and "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) > 0

    def test_create_full_template_with_yarn(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with full template uses correct yarn command for Vite."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "yarn-vite-project",
                    "--template",
                    "full",
                    "--package-manager",
                    "yarn",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Find the create-vite call and verify it uses yarn syntax
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "yarn" in str(call) and "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) > 0

    def test_create_full_template_with_bun(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Create with full template uses correct bun command for Vite."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                main,
                [
                    "create",
                    "bun-vite-project",
                    "--template",
                    "full",
                    "--package-manager",
                    "bun",
                    "--no-install",
                    "--no-git",
                    "-y",
                ],
            )

            assert result.exit_code == 0

            # Find the create-vite call and verify it uses bun syntax
            vite_calls = [
                call
                for call in mock_subprocess.call_args_list
                if "bun" in str(call) and "create" in str(call) and "vite" in str(call)
            ]
            assert len(vite_calls) > 0
