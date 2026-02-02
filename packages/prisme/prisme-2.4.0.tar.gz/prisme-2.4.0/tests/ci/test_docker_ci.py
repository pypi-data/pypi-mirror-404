"""Tests for Docker CI/CD workflow generation."""

import pytest

from prisme.ci.docker import DockerCIGenerator


class TestDockerCIGenerator:
    """Test DockerCIGenerator."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project directory."""
        project_dir = tmp_path / "testproject"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def generator(self, temp_project):
        """Create DockerCIGenerator instance."""
        return DockerCIGenerator(temp_project)

    def test_generator_initialization(self, temp_project):
        """Test generator initialization."""
        generator = DockerCIGenerator(temp_project)
        assert generator.project_dir == temp_project
        assert generator.workflows_dir == temp_project / ".github" / "workflows"

    def test_generate_docker_build_workflow(self, generator, temp_project):
        """Test Docker build workflow generation."""
        generator.generate_docker_build_workflow()

        workflow_file = temp_project / ".github" / "workflows" / "docker-build.yml"
        assert workflow_file.exists()

        content = workflow_file.read_text()

        # Check workflow name
        assert "name: Docker Build" in content

        # Check triggers
        assert "on:" in content
        assert "push:" in content
        assert "pull_request:" in content
        assert "release:" in content

        # Check jobs
        assert "build-backend:" in content
        assert "build-frontend:" in content
        assert "test-images:" in content
        assert "security-scan:" in content

        # Check GitHub Container Registry
        assert "REGISTRY: ghcr.io" in content
        # IMAGE_NAME is set dynamically to lowercase the repository name
        assert "Set lowercase image name" in content
        assert "GITHUB_REPOSITORY,," in content  # Bash lowercase expansion

        # Check Docker actions
        assert "docker/setup-buildx-action@v3" in content
        assert "docker/login-action@v3" in content
        assert "docker/metadata-action@v5" in content
        assert "docker/build-push-action@v5" in content

        # Check Trivy security scanning
        assert "aquasecurity/trivy-action@master" in content
        assert "trivy-backend-results.sarif" in content
        assert "trivy-frontend-results.sarif" in content

    def test_workflow_uses_production_dockerfiles(self, generator, temp_project):
        """Test that workflow references production Dockerfiles."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        assert "Dockerfile.backend.prod" in content
        assert "Dockerfile.frontend.prod" in content

    def test_workflow_has_image_tagging_strategy(self, generator, temp_project):
        """Test that workflow has proper image tagging."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        # Check tagging strategies
        assert "type=ref,event=branch" in content
        assert "type=ref,event=pr" in content
        assert "type=semver,pattern" in content
        assert "type=sha,prefix" in content

    def test_workflow_has_caching(self, generator, temp_project):
        """Test that workflow uses GitHub Actions caching."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        assert "cache-from: type=gha" in content
        assert "cache-to: type=gha,mode=max" in content

    def test_workflow_runs_integration_tests(self, generator, temp_project):
        """Test that workflow runs integration tests on PR."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        # Check test-images job
        assert "test-images:" in content
        assert "docker compose -f docker-compose.prod.yml" in content
        assert "Wait for services to be healthy" in content
        assert "Test backend health endpoint" in content
        assert "Test frontend health endpoint" in content

    def test_workflow_has_security_scanning(self, generator, temp_project):
        """Test that workflow includes security scanning."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        # Check security-scan job
        assert "security-scan:" in content
        assert "Trivy vulnerability scanner" in content
        assert "github/codeql-action/upload-sarif@v2" in content
        assert "backend-image" in content
        assert "frontend-image" in content

    def test_extend_ci_with_docker_tests_file_not_found(self, generator, temp_project, capsys):
        """Test extending CI when ci.yml doesn't exist."""
        generator.extend_ci_with_docker_tests()

        capsys.readouterr()
        # The warning is printed via Rich console, so we just verify no exception

    def test_extend_ci_with_docker_tests_success(self, generator, temp_project):
        """Test successfully extending CI workflow."""
        # Create a basic ci.yml file
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        generator.extend_ci_with_docker_tests()

        content = ci_file.read_text()

        # Check that Docker tests were added
        assert "test-in-docker:" in content
        assert "Integration Tests (Docker)" in content
        assert "docker compose -f docker-compose.dev.yml" in content
        assert "pytest --cov" in content
        assert "npm run test" in content

    def test_extend_ci_idempotent(self, generator, temp_project):
        """Test that extending CI is idempotent."""
        # Create a basic ci.yml file
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        # Run twice
        generator.extend_ci_with_docker_tests()
        content_first = ci_file.read_text()

        generator.extend_ci_with_docker_tests()
        content_second = ci_file.read_text()

        # Second run should not duplicate content
        assert content_first == content_second

    def test_docker_tests_template_structure(self, generator, temp_project):
        """Test Docker tests template has correct structure."""
        # Create a basic ci.yml file
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        generator.extend_ci_with_docker_tests()

        content = ci_file.read_text()

        # Check job structure
        assert "test-in-docker:" in content
        assert "runs-on: ubuntu-latest" in content
        assert "needs: [backend-lint, frontend-lint]" in content

        # Check steps
        assert "Set up Docker Buildx" in content
        assert "Build development images" in content
        assert "Start services" in content
        assert "Wait for services to be healthy" in content
        assert "Run backend tests in container" in content
        assert "Run frontend tests in container" in content
        assert "Collect logs on failure" in content
        assert "Tear down" in content

    def test_docker_tests_wait_for_healthy(self, generator, temp_project):
        """Test that Docker tests wait for healthy services."""
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        generator.extend_ci_with_docker_tests()

        content = ci_file.read_text()

        # Check health check waiting
        assert "timeout 90" in content
        assert 'grep -q "healthy"' in content

    def test_docker_tests_cleanup_on_failure(self, generator, temp_project):
        """Test that Docker tests clean up on failure."""
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        generator.extend_ci_with_docker_tests()

        content = ci_file.read_text()

        # Check cleanup steps
        assert "if: failure()" in content
        assert "if: always()" in content
        assert "docker compose" in content and "down -v" in content

    def test_workflow_permissions(self, generator, temp_project):
        """Test that workflow has correct permissions."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        # Check permissions
        assert "permissions:" in content
        assert "contents: read" in content
        assert "packages: write" in content
        assert "security-events: write" in content

    def test_workflow_conditional_push(self, generator, temp_project):
        """Test that images are only pushed on non-PR events."""
        generator.generate_docker_build_workflow()

        content = (temp_project / ".github" / "workflows" / "docker-build.yml").read_text()

        # Check conditional push
        assert "github.event_name != 'pull_request'" in content

    def test_full_docker_ci_setup(self, generator, temp_project):
        """Test full Docker CI setup."""
        # Create basic ci.yml
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text("name: CI\n\njobs:\n  backend-lint:\n    runs-on: ubuntu-latest\n")

        # Generate both workflows
        generator.generate_docker_build_workflow()
        generator.extend_ci_with_docker_tests()

        # Check both files exist
        assert (workflows_dir / "docker-build.yml").exists()
        assert ci_file.exists()

        # Check both have Docker content
        docker_build_content = (workflows_dir / "docker-build.yml").read_text()
        ci_content = ci_file.read_text()

        assert "Docker Build" in docker_build_content
        assert "test-in-docker:" in ci_content
