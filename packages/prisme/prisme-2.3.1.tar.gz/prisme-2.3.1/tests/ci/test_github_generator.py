"""Tests for GitHub Actions CI/CD generation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from prisme.ci.github import CIConfig, GitHubCIGenerator


class TestGitHubCIGenerator:
    """Test GitHub CI/CD generation."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        """Basic CI configuration."""
        return CIConfig(
            project_name="testproject",
            include_frontend=True,
            use_redis=False,
            enable_codecov=True,
            enable_dependabot=True,
        )

    @pytest.fixture
    def minimal_config(self):
        """Minimal CI configuration (backend only)."""
        return CIConfig(
            project_name="minimalproject",
            include_frontend=False,
            use_redis=False,
            enable_codecov=False,
            enable_dependabot=False,
        )

    def test_generator_creates_directories(self, temp_project_dir, basic_config):
        """Test that generator creates necessary directories."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        assert (temp_project_dir / ".github").exists()
        assert (temp_project_dir / ".github" / "workflows").exists()

    def test_generator_creates_ci_workflow(self, temp_project_dir, basic_config):
        """Test that CI workflow is generated."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        assert ci_file.exists()

        # Verify it's valid YAML
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            assert workflow["name"] == "CI"
            assert "jobs" in workflow

    def test_ci_workflow_includes_backend_jobs(self, temp_project_dir, basic_config):
        """Test that CI workflow includes all backend jobs."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            jobs = workflow["jobs"]

            # Check backend jobs exist
            assert "backend-lint" in jobs
            assert "backend-typecheck" in jobs
            assert "backend-test" in jobs

    def test_ci_workflow_includes_frontend_jobs_when_enabled(self, temp_project_dir, basic_config):
        """Test that frontend jobs are included when frontend is enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            jobs = workflow["jobs"]

            # Check frontend jobs exist
            assert "frontend-lint" in jobs
            assert "frontend-typecheck" in jobs
            assert "frontend-test" in jobs

    def test_ci_workflow_excludes_frontend_jobs_when_disabled(
        self, temp_project_dir, minimal_config
    ):
        """Test that frontend jobs are excluded when frontend is disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(minimal_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            jobs = workflow["jobs"]

            # Check frontend jobs don't exist
            assert "frontend-lint" not in jobs
            assert "frontend-typecheck" not in jobs
            assert "frontend-test" not in jobs

    def test_ci_workflow_includes_postgres_service(self, temp_project_dir, basic_config):
        """Test that PostgreSQL service is configured in backend-test."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            backend_test = workflow["jobs"]["backend-test"]

            assert "services" in backend_test
            assert "postgres" in backend_test["services"]

    def test_ci_workflow_includes_redis_when_enabled(self, temp_project_dir):
        """Test that Redis service is included when enabled."""
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
            use_redis=True,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            backend_test = workflow["jobs"]["backend-test"]

            assert "redis" in backend_test["services"]

    def test_ci_workflow_excludes_redis_when_disabled(self, temp_project_dir, minimal_config):
        """Test that Redis service is excluded when disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(minimal_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)
            backend_test = workflow["jobs"]["backend-test"]

            assert "redis" not in backend_test.get("services", {})

    def test_ci_workflow_includes_codecov_when_enabled(self, temp_project_dir, basic_config):
        """Test that Codecov upload step is included when enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "codecov" in content.lower()
        assert "CODECOV_TOKEN" in content

    def test_ci_workflow_excludes_codecov_when_disabled(self, temp_project_dir, minimal_config):
        """Test that Codecov upload step is excluded when disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(minimal_config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "codecov" not in content.lower()

    def test_ci_workflow_uses_correct_python_version(self, temp_project_dir):
        """Test that CI workflow uses specified Python version."""
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
            python_version="3.12",
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "python-version: '3.12'" in content

    def test_ci_workflow_uses_correct_node_version(self, temp_project_dir):
        """Test that CI workflow uses specified Node version."""
        config = CIConfig(
            project_name="testproject",
            include_frontend=True,
            node_version="20",
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "node-version: '20'" in content

    def test_generator_creates_dependabot_when_enabled(self, temp_project_dir, basic_config):
        """Test that Dependabot config is generated when enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        assert dependabot_file.exists()

        # Verify it's valid YAML
        with dependabot_file.open() as f:
            config = yaml.safe_load(f)
            assert config["version"] == 2
            assert "updates" in config

    def test_generator_skips_dependabot_when_disabled(self, temp_project_dir, minimal_config):
        """Test that Dependabot config is not generated when disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(minimal_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        assert not dependabot_file.exists()

    def test_dependabot_includes_pip_ecosystem(self, temp_project_dir, basic_config):
        """Test that Dependabot config includes pip ecosystem."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        with dependabot_file.open() as f:
            config = yaml.safe_load(f)
            ecosystems = [update["package-ecosystem"] for update in config["updates"]]

            assert "pip" in ecosystems

    def test_dependabot_includes_npm_when_frontend_enabled(self, temp_project_dir, basic_config):
        """Test that Dependabot config includes npm when frontend is enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        with dependabot_file.open() as f:
            config = yaml.safe_load(f)
            ecosystems = [update["package-ecosystem"] for update in config["updates"]]

            assert "npm" in ecosystems

    def test_dependabot_excludes_npm_when_frontend_disabled(self, temp_project_dir, minimal_config):
        """Test that Dependabot config excludes npm when frontend is disabled."""
        # Enable dependabot for this test
        minimal_config.enable_dependabot = True

        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(minimal_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        with dependabot_file.open() as f:
            config = yaml.safe_load(f)
            ecosystems = [update["package-ecosystem"] for update in config["updates"]]

            assert "npm" not in ecosystems

    def test_dependabot_includes_github_actions(self, temp_project_dir, basic_config):
        """Test that Dependabot config includes github-actions ecosystem."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(basic_config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        with dependabot_file.open() as f:
            config = yaml.safe_load(f)
            ecosystems = [update["package-ecosystem"] for update in config["updates"]]

            assert "github-actions" in ecosystems

    def test_dependabot_includes_reviewer_when_specified(self, temp_project_dir):
        """Test that Dependabot config includes reviewer when specified."""
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
            enable_dependabot=True,
            github_username="testuser",
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        dependabot_file = temp_project_dir / ".github" / "dependabot.yml"
        content = dependabot_file.read_text()

        assert "testuser" in content
        assert "reviewers:" in content
