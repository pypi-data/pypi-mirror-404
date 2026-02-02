"""Tests for semantic release generation."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from prisme.ci.github import CIConfig, GitHubCIGenerator


class TestSemanticRelease:
    """Test semantic release generation."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def full_config(self):
        """Full CI configuration with semantic release."""
        return CIConfig(
            project_name="testproject",
            include_frontend=True,
            use_redis=False,
            enable_semantic_release=True,
            enable_commitlint=True,
        )

    @pytest.fixture
    def no_release_config(self):
        """CI configuration without semantic release."""
        return CIConfig(
            project_name="testproject",
            include_frontend=False,
            enable_semantic_release=False,
            enable_commitlint=False,
        )

    def test_generator_creates_release_workflow_when_enabled(self, temp_project_dir, full_config):
        """Test that release workflow is generated when enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        assert release_file.exists()

    def test_generator_skips_release_workflow_when_disabled(
        self, temp_project_dir, no_release_config
    ):
        """Test that release workflow is not generated when disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(no_release_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        assert not release_file.exists()

    def test_release_workflow_is_valid_yaml(self, temp_project_dir, full_config):
        """Test that release workflow is valid YAML."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        with release_file.open() as f:
            workflow = yaml.safe_load(f)
            assert workflow["name"] == "Release"
            assert "jobs" in workflow
            assert "release" in workflow["jobs"]

    def test_release_workflow_triggers_on_main_push(self, temp_project_dir, full_config):
        """Test that release workflow triggers on push to main."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        with release_file.open() as f:
            workflow = yaml.safe_load(f)
            # 'on' is a reserved keyword in YAML, so it gets parsed as True
            on_config = workflow[True]

            assert "push" in on_config
            assert "branches" in on_config["push"]
            assert "main" in on_config["push"]["branches"]

    def test_release_workflow_has_correct_permissions(self, temp_project_dir, full_config):
        """Test that release workflow has correct permissions."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        with release_file.open() as f:
            workflow = yaml.safe_load(f)
            permissions = workflow.get("permissions", {})

            assert permissions.get("contents") == "write"
            assert permissions.get("issues") == "write"
            assert permissions.get("pull-requests") == "write"

    def test_generator_creates_releaserc_config(self, temp_project_dir, full_config):
        """Test that .releaserc.json is generated."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        releaserc_file = temp_project_dir / ".releaserc.json"
        assert releaserc_file.exists()

        # Verify it's valid JSON
        with releaserc_file.open() as f:
            config = json.load(f)
            assert "branches" in config
            assert "plugins" in config

    def test_releaserc_includes_required_plugins(self, temp_project_dir, full_config):
        """Test that .releaserc.json includes all required plugins."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        releaserc_file = temp_project_dir / ".releaserc.json"
        with releaserc_file.open() as f:
            config = json.load(f)
            plugins = [
                plugin[0] if isinstance(plugin, list) else plugin for plugin in config["plugins"]
            ]

            assert "@semantic-release/commit-analyzer" in plugins
            assert "@semantic-release/release-notes-generator" in plugins
            assert "@semantic-release/changelog" in plugins
            assert "@semantic-release/github" in plugins
            assert "@semantic-release/git" in plugins

    def test_releaserc_configures_conventional_commits(self, temp_project_dir, full_config):
        """Test that .releaserc.json uses conventional commits preset."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        releaserc_file = temp_project_dir / ".releaserc.json"
        with releaserc_file.open() as f:
            config = json.load(f)

            # Find commit-analyzer plugin config
            for plugin in config["plugins"]:
                if isinstance(plugin, list) and plugin[0] == "@semantic-release/commit-analyzer":
                    assert plugin[1]["preset"] == "conventionalcommits"
                    break
            else:
                pytest.fail("commit-analyzer plugin not found")

    def test_releaserc_includes_release_rules(self, temp_project_dir, full_config):
        """Test that .releaserc.json includes proper release rules."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        releaserc_file = temp_project_dir / ".releaserc.json"
        with releaserc_file.open() as f:
            config = json.load(f)

            # Find commit-analyzer plugin config
            for plugin in config["plugins"]:
                if isinstance(plugin, list) and plugin[0] == "@semantic-release/commit-analyzer":
                    rules = plugin[1]["releaseRules"]
                    rule_types = {rule["type"] for rule in rules}

                    assert "feat" in rule_types
                    assert "fix" in rule_types
                    assert "perf" in rule_types
                    break
            else:
                pytest.fail("commit-analyzer plugin not found")

    def test_generator_creates_commitlint_config_when_enabled(self, temp_project_dir, full_config):
        """Test that commitlint.config.js is generated when enabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        commitlint_file = temp_project_dir / "commitlint.config.js"
        assert commitlint_file.exists()

    def test_generator_skips_commitlint_config_when_disabled(
        self, temp_project_dir, no_release_config
    ):
        """Test that commitlint.config.js is not generated when disabled."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(no_release_config)

        commitlint_file = temp_project_dir / "commitlint.config.js"
        assert not commitlint_file.exists()

    def test_commitlint_config_includes_conventional_types(self, temp_project_dir, full_config):
        """Test that commitlint config includes all conventional commit types."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        commitlint_file = temp_project_dir / "commitlint.config.js"
        content = commitlint_file.read_text()

        # Check for required commit types
        assert "'feat'" in content
        assert "'fix'" in content
        assert "'docs'" in content
        assert "'style'" in content
        assert "'refactor'" in content
        assert "'perf'" in content
        assert "'test'" in content
        assert "'build'" in content
        assert "'ci'" in content
        assert "'chore'" in content
        assert "'revert'" in content

    def test_generator_creates_changelog(self, temp_project_dir, full_config):
        """Test that CHANGELOG.md is generated."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        changelog_file = temp_project_dir / "CHANGELOG.md"
        assert changelog_file.exists()

    def test_changelog_has_correct_format(self, temp_project_dir, full_config):
        """Test that CHANGELOG.md has correct format."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        changelog_file = temp_project_dir / "CHANGELOG.md"
        content = changelog_file.read_text()

        assert "# Changelog" in content
        assert "[Unreleased]" in content
        assert "semantic-release" in content

    def test_changelog_not_overwritten_if_exists(self, temp_project_dir, full_config):
        """Test that existing CHANGELOG.md is not overwritten."""
        existing_content = "# My Custom Changelog\n\nDon't overwrite me!"
        changelog_file = temp_project_dir / "CHANGELOG.md"
        changelog_file.write_text(existing_content)

        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        # Verify content hasn't changed
        assert changelog_file.read_text() == existing_content

    def test_release_workflow_uses_correct_node_version(self, temp_project_dir):
        """Test that release workflow uses specified Node version."""
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
            node_version="20",
            enable_semantic_release=True,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        content = release_file.read_text()

        assert "node-version: '20'" in content

    def test_release_workflow_includes_semantic_release_dependencies(
        self, temp_project_dir, full_config
    ):
        """Test that release workflow installs semantic-release dependencies."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        release_file = temp_project_dir / ".github" / "workflows" / "release.yml"
        content = release_file.read_text()

        assert "semantic-release" in content
        assert "@semantic-release/changelog" in content
        assert "@semantic-release/git" in content
        assert "@semantic-release/github" in content
        assert "conventional-changelog-conventionalcommits" in content

    def test_full_ci_cd_generation(self, temp_project_dir, full_config):
        """Test that full CI/CD setup generates all expected files."""
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(full_config)

        # Check all expected files exist
        assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists()
        assert (temp_project_dir / ".github" / "workflows" / "release.yml").exists()
        assert (temp_project_dir / ".github" / "dependabot.yml").exists()
        assert (temp_project_dir / ".releaserc.json").exists()
        assert (temp_project_dir / "commitlint.config.js").exists()
        assert (temp_project_dir / "CHANGELOG.md").exists()
