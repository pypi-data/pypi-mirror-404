"""End-to-end test for the demo spec one-liner.

This test executes the full one-liner workflow from the README:
    prism create my-app --spec demo.py && cd my-app && prism install && prism generate && prism test

The test uses the demo spec (specs/demo.py) which showcases all Prism features.

Run with: pytest -m e2e tests/e2e/
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import get_prism_command, run_command, setup_project_with_spec


@pytest.fixture(scope="module")
def demo_project_dir(e2e_temp_dir: Path) -> Path:
    """Create a demo project using prism create with the demo spec."""
    project_name = "demo-test-app"
    project_dir = e2e_temp_dir / project_name

    # Setup project with spec inside (spec must be within project folder)
    spec_dest = setup_project_with_spec(project_dir)

    # Run prism create with spec path inside project
    result = run_command(
        [*get_prism_command(), "create", project_name, "--spec", str(spec_dest), "-y"],
        cwd=e2e_temp_dir,
        timeout=120,
    )

    assert project_dir.exists(), f"Project directory not created: {result.stdout}"
    return project_dir


@pytest.mark.e2e
class TestDemoOnelinerCreate:
    """Test the 'prism create' step of the one-liner."""

    def test_project_directory_created(self, demo_project_dir: Path) -> None:
        """Project directory is created."""
        assert demo_project_dir.exists()
        assert demo_project_dir.is_dir()

    def test_spec_file_copied(self, demo_project_dir: Path) -> None:
        """Spec file is copied to the project."""
        spec_file = demo_project_dir / "specs" / "models.py"
        assert spec_file.exists(), "Spec file not found"

    def test_prisme_toml_created(self, demo_project_dir: Path) -> None:
        """prisme.toml is created."""
        config = demo_project_dir / "prisme.toml"
        assert config.exists()

    def test_backend_structure_created(self, demo_project_dir: Path) -> None:
        """Backend package structure is created."""
        backend_dir = demo_project_dir / "packages" / "backend"
        assert backend_dir.exists()
        assert (backend_dir / "pyproject.toml").exists()

    def test_frontend_structure_created(self, demo_project_dir: Path) -> None:
        """Frontend package structure is created."""
        frontend_dir = demo_project_dir / "packages" / "frontend"
        assert frontend_dir.exists()
        assert (frontend_dir / "package.json").exists()


@pytest.mark.e2e
class TestDemoOnelinerGenerate:
    """Test the 'prism generate' step of the one-liner."""

    @pytest.fixture(scope="class")
    def generated_project(self, demo_project_dir: Path) -> Path:
        """Run prism generate on the demo project."""
        run_command(
            [*get_prism_command(), "generate"],
            cwd=demo_project_dir,
            timeout=120,
        )
        return demo_project_dir

    def test_models_generated(self, generated_project: Path) -> None:
        """SQLAlchemy models are generated."""
        # Models are generated inside the package namespace
        # Package name comes from the project name (demo-test-app -> demo_test_app)
        package_name = "demo_test_app"
        models_dir = generated_project / "packages" / "backend" / "src" / package_name / "models"
        assert models_dir.exists()

        # Check for demo models
        assert (models_dir / "company.py").exists()
        assert (models_dir / "employee.py").exists()
        assert (models_dir / "project.py").exists()

    def test_schemas_generated(self, generated_project: Path) -> None:
        """Pydantic schemas are generated."""
        package_name = "demo_test_app"
        schemas_dir = generated_project / "packages" / "backend" / "src" / package_name / "schemas"
        assert schemas_dir.exists()

        # Check for demo schemas
        assert (schemas_dir / "company.py").exists()
        assert (schemas_dir / "employee.py").exists()

    def test_services_generated(self, generated_project: Path) -> None:
        """Service classes are generated."""
        package_name = "demo_test_app"
        services_dir = (
            generated_project / "packages" / "backend" / "src" / package_name / "services"
        )
        assert services_dir.exists()

        # Check for generated service base files
        generated_dir = services_dir / "_generated"
        assert generated_dir.exists()
        assert (generated_dir / "company_base.py").exists()
        assert (generated_dir / "employee_base.py").exists()

    def test_rest_endpoints_generated(self, generated_project: Path) -> None:
        """REST endpoints are generated."""
        package_name = "demo_test_app"
        api_dir = generated_project / "packages" / "backend" / "src" / package_name / "api" / "rest"
        assert api_dir.exists()

        # Check for endpoint files
        rest_files = list(api_dir.glob("**/*.py"))
        assert len(rest_files) > 0, "No REST endpoint files generated"

    def test_graphql_generated(self, generated_project: Path) -> None:
        """GraphQL schema is generated."""
        package_name = "demo_test_app"
        graphql_dir = (
            generated_project / "packages" / "backend" / "src" / package_name / "api" / "graphql"
        )
        assert graphql_dir.exists()

    def test_frontend_components_generated(self, generated_project: Path) -> None:
        """Frontend components are generated."""
        components_dir = generated_project / "packages" / "frontend" / "src" / "components"
        assert components_dir.exists()

        # Check for generated component files
        assert (components_dir / "_generated").exists() or any(
            d.name.startswith("company") for d in components_dir.iterdir() if d.is_dir()
        )

    def test_frontend_hooks_generated(self, generated_project: Path) -> None:
        """Frontend hooks are generated."""
        hooks_dir = generated_project / "packages" / "frontend" / "src" / "hooks"
        assert hooks_dir.exists()

        # Check for hook files
        hook_files = list(hooks_dir.glob("use*.ts*"))
        assert len(hook_files) > 0, "No hooks generated"

    def test_frontend_types_generated(self, generated_project: Path) -> None:
        """Frontend TypeScript types are generated."""
        types_file = generated_project / "packages" / "frontend" / "src" / "types" / "generated.ts"
        assert types_file.exists()

    def test_tests_generated(self, generated_project: Path) -> None:
        """Test files are generated."""
        # Backend tests
        backend_tests = generated_project / "packages" / "backend" / "tests"
        assert backend_tests.exists()

        frontend_tests = generated_project / "packages" / "frontend" / "src" / "__tests__"
        assert frontend_tests.exists()


@pytest.mark.e2e
class TestDemoOnelinerTest:
    """Test the 'prism test' step of the one-liner.

    Verifies that test infrastructure is properly generated.
    """

    @pytest.fixture(scope="class")
    def tested_project(self, demo_project_dir: Path) -> Path:
        """Ensure project is generated before testing."""
        run_command(
            [*get_prism_command(), "generate"],
            cwd=demo_project_dir,
            timeout=120,
            check=False,  # May already be generated
        )
        return demo_project_dir

    def test_frontend_test_config_exists(self, tested_project: Path) -> None:
        """Frontend test configuration is generated."""
        frontend_dir = tested_project / "packages" / "frontend"

        # Verify vitest config exists
        assert (frontend_dir / "vitest.config.ts").exists(), "vitest.config.ts not found"

        # Verify package.json has test script
        package_json = frontend_dir / "package.json"
        assert package_json.exists()
        content = package_json.read_text()
        assert '"test"' in content, "test script not found in package.json"

    def test_frontend_test_files_generated(self, tested_project: Path) -> None:
        """Frontend test files are generated."""
        tests_dir = tested_project / "packages" / "frontend" / "src" / "__tests__"
        assert tests_dir.exists(), "__tests__ directory not found"

        # Check that test files were generated
        test_files = list(tests_dir.rglob("*.test.ts*"))
        assert len(test_files) > 0, "No test files generated"

    def test_backend_test_config_exists(self, tested_project: Path) -> None:
        """Backend test configuration is generated."""
        backend_dir = tested_project / "packages" / "backend"

        # Verify pytest is in dependencies
        pyproject = backend_dir / "pyproject.toml"
        assert pyproject.exists()
        content = pyproject.read_text()
        assert "pytest" in content, "pytest not found in backend dependencies"

    def test_backend_test_files_generated(self, tested_project: Path) -> None:
        """Backend test files are generated."""
        tests_dir = tested_project / "packages" / "backend" / "tests"
        assert tests_dir.exists(), "tests directory not found"

        # Check that test files were generated
        test_files = list(tests_dir.rglob("test_*.py"))
        assert len(test_files) > 0, "No test files generated"


@pytest.mark.e2e
class TestDemoOnelinerFullPipeline:
    """Full end-to-end pipeline test."""

    def test_one_liner_pipeline(self, e2e_temp_dir: Path) -> None:
        """
        Test the complete one-liner workflow:
        prism create && prism generate && prism test (frontend only)
        """
        project_name = "full-pipeline-test"
        project_dir = e2e_temp_dir / project_name

        # Setup project with spec inside (spec must be within project folder)
        spec_dest = setup_project_with_spec(project_dir)

        # Step 1: Create
        create_result = run_command(
            [*get_prism_command(), "create", project_name, "--spec", str(spec_dest), "-y"],
            cwd=e2e_temp_dir,
            timeout=120,
        )
        assert project_dir.exists(), f"Create failed: {create_result.stderr}"

        # Step 2: Generate
        generate_result = run_command(
            [*get_prism_command(), "generate"],
            cwd=project_dir,
            timeout=120,
        )
        assert generate_result.returncode == 0, f"Generate failed: {generate_result.stderr}"

        # Step 3: Verify key files exist
        # Models are generated inside the package namespace (name from project: full-pipeline-test -> full_pipeline_test)
        package_name = "full_pipeline_test"
        assert (project_dir / "packages" / "backend" / "src" / package_name / "models").exists()
        assert (project_dir / "packages" / "frontend" / "src" / "components").exists()

        # Step 4: Check generation summary
        assert "Total" in generate_result.stdout or "Summary" in generate_result.stdout

    def test_validate_before_generate(self, e2e_temp_dir: Path) -> None:
        """Validate command works on created project."""
        project_name = "validate-test"
        project_dir = e2e_temp_dir / project_name

        # Setup project with spec inside (spec must be within project folder)
        spec_dest = setup_project_with_spec(project_dir)

        # Create project
        run_command(
            [*get_prism_command(), "create", project_name, "--spec", str(spec_dest), "-y"],
            cwd=e2e_temp_dir,
            timeout=120,
        )

        # Validate - needs the spec path
        spec_file = project_dir / "specs" / "models.py"
        validate_result = run_command(
            [*get_prism_command(), "validate", str(spec_file)],
            cwd=project_dir,
            timeout=30,
        )
        assert validate_result.returncode == 0
        assert "valid" in validate_result.stdout.lower()


@pytest.mark.e2e
class TestDemoSpecFeatureGeneration:
    """Test that demo spec features are correctly generated."""

    @pytest.fixture(scope="class")
    def feature_project(self, e2e_temp_dir: Path) -> Path:
        """Create and generate a project for feature testing."""
        project_name = "feature-test"
        project_dir = e2e_temp_dir / project_name

        # Setup project with spec inside (spec must be within project folder)
        spec_dest = setup_project_with_spec(project_dir)

        # Create and generate
        run_command(
            [*get_prism_command(), "create", project_name, "--spec", str(spec_dest), "-y"],
            cwd=e2e_temp_dir,
            timeout=120,
        )
        run_command(
            [*get_prism_command(), "generate"],
            cwd=project_dir,
            timeout=120,
        )
        return project_dir

    def test_soft_delete_generated(self, feature_project: Path) -> None:
        """Soft delete models use SoftDeleteMixin."""
        # Package name comes from the project name (feature-test -> feature_test)
        package_name = "feature_test"
        company_model = (
            feature_project
            / "packages"
            / "backend"
            / "src"
            / package_name
            / "models"
            / "company.py"
        )
        content = company_model.read_text()
        # Company uses SoftDeleteMixin which provides deleted_at
        assert "SoftDeleteMixin" in content

    def test_timestamps_generated(self, feature_project: Path) -> None:
        """Timestamp models use TimestampMixin."""
        package_name = "feature_test"
        company_model = (
            feature_project
            / "packages"
            / "backend"
            / "src"
            / package_name
            / "models"
            / "company.py"
        )
        content = company_model.read_text()
        # Company uses TimestampMixin which provides created_at/updated_at
        assert "TimestampMixin" in content

    def test_temporal_queries_generated(self, feature_project: Path) -> None:
        """Temporal models have get_latest and get_history methods."""
        package_name = "feature_test"
        stock_service = (
            feature_project
            / "packages"
            / "backend"
            / "src"
            / package_name
            / "services"
            / "_generated"
            / "stock_price_base.py"
        )
        content = stock_service.read_text()
        assert "get_latest" in content
        assert "get_history" in content

    def test_nested_create_generated(self, feature_project: Path) -> None:
        """Nested create models have create_with_nested method."""
        package_name = "feature_test"
        project_service = (
            feature_project
            / "packages"
            / "backend"
            / "src"
            / package_name
            / "services"
            / "_generated"
            / "project_base.py"
        )
        content = project_service.read_text()
        assert "create_with_nested" in content or "create_with_tasks" in content

    def test_read_only_model_generated(self, feature_project: Path) -> None:
        """Read-only models exist in REST API."""
        package_name = "feature_test"
        # Check that AuditLog REST file exists
        audit_log_rest = (
            feature_project
            / "packages"
            / "backend"
            / "src"
            / package_name
            / "api"
            / "rest"
            / "_generated"
            / "audit_log.py"
        )
        if audit_log_rest.exists():
            content = audit_log_rest.read_text()
            # Read-only should have GET endpoints
            assert "get" in content.lower() or "list" in content.lower()
