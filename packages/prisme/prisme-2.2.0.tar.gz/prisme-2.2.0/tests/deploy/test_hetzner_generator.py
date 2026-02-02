"""Tests for Hetzner deployment generator."""

from pathlib import Path

import pytest

from prisme.deploy import DeploymentConfig, HetznerConfig, HetznerDeployGenerator
from prisme.deploy.config import HetznerLocation, HetznerServerType


class TestHetznerDeployGenerator:
    """Tests for HetznerDeployGenerator."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "testproject"
        project_dir.mkdir()
        # Create .prism directory to simulate initialized project
        (project_dir / ".prisme").mkdir()
        return project_dir

    @pytest.fixture
    def default_config(self) -> DeploymentConfig:
        """Create a default deployment config."""
        return DeploymentConfig(
            project_name="testapp",
            domain="testapp.example.com",
        )

    def test_generator_creates_directory_structure(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that generator creates correct directory structure."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        assert (temp_project / "deploy").exists()
        assert (temp_project / "deploy" / "terraform").exists()
        assert (temp_project / "deploy" / "terraform" / "modules").exists()
        assert (temp_project / "deploy" / "terraform" / "modules" / "server").exists()
        assert (temp_project / "deploy" / "terraform" / "modules" / "volume").exists()
        assert (temp_project / "deploy" / "terraform" / "cloud-init").exists()
        assert (temp_project / "deploy" / "scripts").exists()
        assert (temp_project / "deploy" / "env").exists()

    def test_terraform_files_generated(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that Terraform files are generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        terraform_dir = temp_project / "deploy" / "terraform"
        assert (terraform_dir / "main.tf").exists()
        assert (terraform_dir / "variables.tf").exists()
        assert (terraform_dir / "outputs.tf").exists()
        assert (terraform_dir / "versions.tf").exists()
        assert (terraform_dir / "staging.tfvars").exists()
        assert (terraform_dir / "production.tfvars").exists()

    def test_terraform_modules_generated(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that Terraform modules are generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        modules_dir = temp_project / "deploy" / "terraform" / "modules"

        # Server module
        assert (modules_dir / "server" / "main.tf").exists()
        assert (modules_dir / "server" / "variables.tf").exists()
        assert (modules_dir / "server" / "outputs.tf").exists()

        # Volume module
        assert (modules_dir / "volume" / "main.tf").exists()
        assert (modules_dir / "volume" / "variables.tf").exists()
        assert (modules_dir / "volume" / "outputs.tf").exists()

    def test_cloud_init_generated(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that cloud-init configuration is generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        cloud_init = temp_project / "deploy" / "terraform" / "cloud-init" / "user-data.yml"
        assert cloud_init.exists()

        content = cloud_init.read_text()
        assert "#cloud-config" in content
        assert "docker" in content
        assert "testapp" in content

    def test_github_workflow_generated(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that GitHub Actions workflow is generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        workflow = temp_project / ".github" / "workflows" / "deploy.yml"
        assert workflow.exists()

        content = workflow.read_text()
        assert "Deploy" in content
        assert "staging" in content
        assert "production" in content

    def test_env_templates_generated(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that environment templates are generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        env_dir = temp_project / "deploy" / "env"
        assert (env_dir / ".env.staging.template").exists()
        assert (env_dir / ".env.production.template").exists()

    def test_scripts_generated(self, temp_project: Path, default_config: DeploymentConfig) -> None:
        """Test that deployment scripts are generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        scripts_dir = temp_project / "deploy" / "scripts"
        assert (scripts_dir / "deploy.sh").exists()
        assert (scripts_dir / "rollback.sh").exists()

    def test_scripts_are_executable(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that deployment scripts are executable."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        deploy_script = temp_project / "deploy" / "scripts" / "deploy.sh"
        assert deploy_script.exists()
        # Check executable bit
        assert deploy_script.stat().st_mode & 0o100

    def test_readme_generated(self, temp_project: Path, default_config: DeploymentConfig) -> None:
        """Test that README is generated."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        readme = temp_project / "deploy" / "README.md"
        assert readme.exists()

        content = readme.read_text()
        assert "testapp" in content
        assert "Hetzner" in content

    def test_project_name_in_terraform(
        self, temp_project: Path, default_config: DeploymentConfig
    ) -> None:
        """Test that project name is included in Terraform files."""
        generator = HetznerDeployGenerator(temp_project, default_config)
        generator.generate()

        main_tf = temp_project / "deploy" / "terraform" / "main.tf"
        content = main_tf.read_text()
        assert "testapp" in content

    def test_custom_server_types(self, temp_project: Path) -> None:
        """Test custom server type configuration."""
        hetzner = HetznerConfig(
            staging_server_type=HetznerServerType.CX32,
            production_server_type=HetznerServerType.CX42,
        )
        config = DeploymentConfig(
            project_name="testapp",
            hetzner=hetzner,
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        # Check staging.tfvars
        staging_tfvars = temp_project / "deploy" / "terraform" / "staging.tfvars"
        content = staging_tfvars.read_text()
        assert "cx32" in content

        # Check production.tfvars
        prod_tfvars = temp_project / "deploy" / "terraform" / "production.tfvars"
        content = prod_tfvars.read_text()
        assert "cx42" in content

    def test_custom_location(self, temp_project: Path) -> None:
        """Test custom location configuration."""
        hetzner = HetznerConfig(location=HetznerLocation.HELSINKI)
        config = DeploymentConfig(
            project_name="testapp",
            hetzner=hetzner,
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        staging_tfvars = temp_project / "deploy" / "terraform" / "staging.tfvars"
        content = staging_tfvars.read_text()
        assert "hel1" in content

    def test_redis_enabled(self, temp_project: Path) -> None:
        """Test that Redis configuration is included when enabled."""
        config = DeploymentConfig(
            project_name="testapp",
            use_redis=True,
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        env_template = temp_project / "deploy" / "env" / ".env.staging.template"
        content = env_template.read_text()
        assert "REDIS_URL" in content

    def test_redis_disabled(self, temp_project: Path) -> None:
        """Test that Redis configuration is not included when disabled."""
        config = DeploymentConfig(
            project_name="testapp",
            use_redis=False,
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        env_template = temp_project / "deploy" / "env" / ".env.staging.template"
        content = env_template.read_text()
        # Redis line should not be uncommented
        assert "REDIS_URL=redis://" not in content or "# REDIS_URL" in content

    def test_domain_in_templates(self, temp_project: Path) -> None:
        """Test that domain is included in templates."""
        config = DeploymentConfig(
            project_name="testapp",
            domain="myapp.example.com",
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        readme = temp_project / "deploy" / "README.md"
        content = readme.read_text()
        assert "myapp.example.com" in content

    def test_ssl_email_in_templates(self, temp_project: Path) -> None:
        """Test that SSL email is included in templates."""
        config = DeploymentConfig(
            project_name="testapp",
            ssl_email="admin@example.com",
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        traefik_config = temp_project / "deploy" / "traefik" / "traefik.yml"
        content = traefik_config.read_text()
        assert "admin@example.com" in content

    def test_floating_ip_enabled(self, temp_project: Path) -> None:
        """Test floating IP is enabled by default."""
        config = DeploymentConfig(project_name="testapp")
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        prod_tfvars = temp_project / "deploy" / "terraform" / "production.tfvars"
        content = prod_tfvars.read_text()
        assert "production_floating_ip = true" in content

    def test_floating_ip_disabled(self, temp_project: Path) -> None:
        """Test floating IP can be disabled."""
        hetzner = HetznerConfig(production_floating_ip=False)
        config = DeploymentConfig(
            project_name="testapp",
            hetzner=hetzner,
        )
        generator = HetznerDeployGenerator(temp_project, config)
        generator.generate()

        prod_tfvars = temp_project / "deploy" / "terraform" / "production.tfvars"
        content = prod_tfvars.read_text()
        assert "production_floating_ip = false" in content
