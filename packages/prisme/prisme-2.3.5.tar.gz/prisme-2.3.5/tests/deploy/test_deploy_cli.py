"""Tests for deploy CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from prisme.cli import main


class TestDeployInit:
    """Tests for 'prism deploy init' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_deploy_init_requires_prism_project(self, runner: CliRunner) -> None:
        """Test that deploy init requires a Prism project."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["deploy", "init"])
            assert result.exit_code == 0
            assert "Not a Prism project" in result.output

    def test_deploy_init_creates_files(self, runner: CliRunner) -> None:
        """Test that deploy init creates deployment files."""
        with runner.isolated_filesystem():
            # Create .prism directory to simulate initialized project
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init"])
            assert result.exit_code == 0

            # Check files were created
            assert Path("deploy/terraform/main.tf").exists()
            assert Path("deploy/terraform/variables.tf").exists()
            assert Path("deploy/terraform/staging.tfvars").exists()
            assert Path("deploy/scripts/deploy.sh").exists()
            assert Path(".github/workflows/deploy.yml").exists()

    def test_deploy_init_with_domain(self, runner: CliRunner) -> None:
        """Test deploy init with domain option."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init", "--domain", "example.com"])
            assert result.exit_code == 0

            # Check domain is in templates
            content = Path("deploy/README.md").read_text()
            assert "example.com" in content

    def test_deploy_init_with_custom_location(self, runner: CliRunner) -> None:
        """Test deploy init with custom location."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init", "--location", "hel1"])
            assert result.exit_code == 0

            # Check location is in tfvars
            content = Path("deploy/terraform/staging.tfvars").read_text()
            assert "hel1" in content

    def test_deploy_init_with_custom_server_types(self, runner: CliRunner) -> None:
        """Test deploy init with custom server types."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(
                main,
                [
                    "deploy",
                    "init",
                    "--staging-type",
                    "cx32",
                    "--production-type",
                    "cx42",
                ],
            )
            assert result.exit_code == 0

            # Check server types in tfvars
            staging_content = Path("deploy/terraform/staging.tfvars").read_text()
            assert "cx32" in staging_content

            prod_content = Path("deploy/terraform/production.tfvars").read_text()
            assert "cx42" in prod_content

    def test_deploy_init_with_redis(self, runner: CliRunner) -> None:
        """Test deploy init with Redis enabled."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init", "--redis"])
            assert result.exit_code == 0

            # Check Redis is in env template
            content = Path("deploy/env/.env.staging.template").read_text()
            assert "REDIS_URL" in content

    def test_deploy_init_with_ssl_email(self, runner: CliRunner) -> None:
        """Test deploy init with SSL email."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init", "--ssl-email", "admin@example.com"])
            assert result.exit_code == 0

            # Check SSL email in traefik config
            content = Path("deploy/traefik/traefik.yml").read_text()
            assert "admin@example.com" in content

    def test_deploy_init_no_floating_ip(self, runner: CliRunner) -> None:
        """Test deploy init without floating IP."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            result = runner.invoke(main, ["deploy", "init", "--no-floating-ip"])
            assert result.exit_code == 0

            # Check floating IP is disabled
            content = Path("deploy/terraform/production.tfvars").read_text()
            assert "production_floating_ip = false" in content


class TestDeployStatus:
    """Tests for 'prism deploy status' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_deploy_status_not_initialized(self, runner: CliRunner) -> None:
        """Test deploy status when not initialized."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["deploy", "status"])
            assert result.exit_code == 0
            assert "not initialized" in result.output.lower()

    def test_deploy_status_shows_configuration(self, runner: CliRunner) -> None:
        """Test deploy status shows configuration after init."""
        with runner.isolated_filesystem():
            Path(".prisme").mkdir()

            # Initialize deployment
            runner.invoke(main, ["deploy", "init"])

            # Check status
            result = runner.invoke(main, ["deploy", "status"])
            assert result.exit_code == 0
            assert "Ready" in result.output


class TestDeployPlan:
    """Tests for 'prism deploy plan' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_deploy_plan_not_initialized(self, runner: CliRunner) -> None:
        """Test deploy plan when not initialized."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["deploy", "plan"])
            assert result.exit_code == 0
            assert "not initialized" in result.output.lower()


class TestDeployGroup:
    """Tests for deploy command group."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_deploy_help(self, runner: CliRunner) -> None:
        """Test deploy --help shows available commands."""
        result = runner.invoke(main, ["deploy", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "plan" in result.output
        assert "apply" in result.output
        assert "destroy" in result.output
        assert "ssh" in result.output
        assert "logs" in result.output
        assert "status" in result.output
        assert "ssl" in result.output

    def test_deploy_init_help(self, runner: CliRunner) -> None:
        """Test deploy init --help shows options."""
        result = runner.invoke(main, ["deploy", "init", "--help"])
        assert result.exit_code == 0
        assert "--provider" in result.output
        assert "--domain" in result.output
        assert "--location" in result.output
        assert "--staging-type" in result.output
        assert "--production-type" in result.output
        assert "--ssl-email" in result.output
        assert "--redis" in result.output
