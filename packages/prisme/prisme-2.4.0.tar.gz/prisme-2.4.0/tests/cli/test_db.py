"""Tests for prism db subcommands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.cli import main

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from click.testing import CliRunner


class TestDbMigrateCommand:
    """Tests for the db migrate command."""

    def test_db_migrate_no_alembic_ini(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Shows warning when alembic.ini is missing."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["db", "migrate"])

            assert "alembic" in result.output.lower()

    def test_db_migrate_with_alembic_ini(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Runs alembic when alembic.ini exists."""
        with cli_runner.isolated_filesystem():
            # Create alembic.ini
            Path("alembic.ini").write_text("[alembic]\nscript_location = alembic\n")

            cli_runner.invoke(main, ["db", "migrate"])

            # Should attempt to run alembic
            assert mock_subprocess.called

    def test_db_migrate_with_message(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Creates migration with --message option."""
        with cli_runner.isolated_filesystem():
            Path("alembic.ini").write_text("[alembic]\nscript_location = alembic\n")

            cli_runner.invoke(main, ["db", "migrate", "--message", "Add users table"])

            # Should include the message in alembic call
            assert any("Add users table" in str(call) for call in mock_subprocess.call_args_list)


class TestDbResetCommand:
    """Tests for the db reset command."""

    def test_db_reset_requires_confirmation(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Reset requires user confirmation."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["db", "reset"], input="n\n")

            assert "Aborted" in result.output

    def test_db_reset_with_yes_flag(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Reset with -y skips confirmation."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(main, ["db", "reset", "-y"])

            # Should attempt to run alembic commands
            assert mock_subprocess.called

    def test_db_reset_with_confirmation(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Reset proceeds with user confirmation."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(main, ["db", "reset"], input="y\n")

            # Should attempt to run alembic commands
            assert mock_subprocess.called


class TestDbSeedCommand:
    """Tests for the db seed command."""

    def test_db_seed_no_seed_file(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Shows warning when no seed file found."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["db", "seed"])

            assert "no seed file" in result.output.lower()

    def test_db_seed_with_seed_py(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Runs seed.py when it exists."""
        with cli_runner.isolated_filesystem():
            Path("seed.py").write_text("print('seeding')")

            cli_runner.invoke(main, ["db", "seed"])

            # Should attempt to run the seed script
            assert mock_subprocess.called

    def test_db_seed_with_scripts_seed_py(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """Runs scripts/seed.py when it exists."""
        with cli_runner.isolated_filesystem():
            scripts_dir = Path("scripts")
            scripts_dir.mkdir()
            (scripts_dir / "seed.py").write_text("print('seeding')")

            cli_runner.invoke(main, ["db", "seed"])

            # Should attempt to run the seed script
            assert mock_subprocess.called
