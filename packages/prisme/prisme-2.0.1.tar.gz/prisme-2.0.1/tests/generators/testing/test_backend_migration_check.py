"""Tests for migration check test generation and CI job."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from prisme.ci.github import CIConfig, GitHubCIGenerator
from prisme.generators.base import GeneratorContext
from prisme.generators.testing.backend import BackendTestGenerator
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec


@pytest.fixture
def simple_model() -> ModelSpec:
    return ModelSpec(
        name="Item",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
        ],
    )


@pytest.fixture
def simple_stack(simple_model: ModelSpec) -> StackSpec:
    return StackSpec(
        name="test-migration",
        version="1.0.0",
        models=[simple_model],
    )


@pytest.fixture
def context(simple_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    return GeneratorContext(
        domain_spec=simple_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-migration"),
    )


class TestMigrationCheckTestGeneration:
    """Test that _generate_migration_check_test() produces correct content."""

    def test_generates_migration_check_file(self, context: GeneratorContext) -> None:
        gen = BackendTestGenerator(context)
        result = gen._generate_migration_check_test()

        assert result.path.name == "test_migration_check.py"
        assert "alembic check" in result.content
        assert "@pytest.mark.migration" in result.content

    def test_migration_check_in_shared_files(self, context: GeneratorContext) -> None:
        gen = BackendTestGenerator(context)
        shared = gen.generate_shared_files()

        paths = [f.path.name for f in shared]
        assert "test_migration_check.py" in paths

    def test_migration_check_uses_subprocess(self, context: GeneratorContext) -> None:
        gen = BackendTestGenerator(context)
        result = gen._generate_migration_check_test()

        assert "import subprocess" in result.content
        assert "subprocess.run" in result.content

    def test_migration_check_asserts_returncode(self, context: GeneratorContext) -> None:
        gen = BackendTestGenerator(context)
        result = gen._generate_migration_check_test()

        assert "result.returncode == 0" in result.content


class TestMigrationCheckCIJob:
    """Test that rendered CI YAML includes migration-check job."""

    @pytest.fixture
    def temp_project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_ci_includes_migration_check_job(self, temp_project_dir: Path) -> None:
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)

        assert "migration-check" in workflow["jobs"]

    def test_migration_check_has_postgres_service(self, temp_project_dir: Path) -> None:
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        with ci_file.open() as f:
            workflow = yaml.safe_load(f)

        job = workflow["jobs"]["migration-check"]
        assert "postgres" in job["services"]

    def test_migration_check_runs_alembic_upgrade_and_check(self, temp_project_dir: Path) -> None:
        config = CIConfig(
            project_name="testproject",
            include_frontend=False,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "alembic upgrade head" in content
        assert "alembic check" in content

    def test_migration_check_uses_project_name_in_db(self, temp_project_dir: Path) -> None:
        config = CIConfig(
            project_name="myapp",
            include_frontend=False,
        )
        generator = GitHubCIGenerator(temp_project_dir)
        generator.generate(config)

        ci_file = temp_project_dir / ".github" / "workflows" / "ci.yml"
        content = ci_file.read_text()

        assert "myapp_migration_check" in content
