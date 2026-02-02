"""Tests for ProjectSpec model."""

from prisme.spec.project import (
    BackendConfig,
    CIConfig,
    DatabaseConfig,
    DeployConfig,
    DockerConfig,
    DockerProductionConfig,
    ExposureConfig,
    FrontendConfig,
    ProjectSpec,
)


class TestProjectSpec:
    def test_minimal(self):
        spec = ProjectSpec(name="my-app")
        assert spec.name == "my-app"
        assert spec.effective_title == "My App"
        assert spec.backend.framework == "fastapi"
        assert spec.frontend.enabled is True
        assert spec.database.engine == "postgresql"

    def test_with_title(self):
        spec = ProjectSpec(name="my-app", title="My Application")
        assert spec.effective_title == "My Application"

    def test_database_config(self):
        db = DatabaseConfig(engine="sqlite", async_driver=False)
        spec = ProjectSpec(name="test", database=db)
        assert spec.database.engine == "sqlite"
        assert spec.database.async_driver is False

    def test_exposure_config(self):
        spec = ProjectSpec(name="test")
        assert spec.exposure.rest.enabled is True
        assert spec.exposure.graphql.enabled is True
        assert spec.exposure.mcp.enabled is True
        assert spec.exposure.frontend.enabled is True

    def test_backend_config(self):
        backend = BackendConfig(port=9000, module_name="my_mod")
        spec = ProjectSpec(name="test", backend=backend)
        assert spec.backend.port == 9000
        assert spec.backend.module_name == "my_mod"

    def test_frontend_disabled(self):
        frontend = FrontendConfig(enabled=False)
        spec = ProjectSpec(name="test", frontend=frontend)
        assert spec.frontend.enabled is False

    def test_deploy_config(self):
        spec = ProjectSpec(
            name="test", deploy=DeployConfig(provider="hetzner", domain="example.com")
        )
        assert spec.deploy is not None
        assert spec.deploy.provider == "hetzner"
        assert spec.deploy.domain == "example.com"
        assert spec.deploy.hetzner.location == "fsn1"

    def test_deploy_none_by_default(self):
        spec = ProjectSpec(name="test")
        assert spec.deploy is None

    def test_ci_config(self):
        spec = ProjectSpec(name="test", ci=CIConfig(use_redis=True, enable_codecov=False))
        assert spec.ci is not None
        assert spec.ci.use_redis is True
        assert spec.ci.enable_codecov is False
        assert spec.ci.provider == "github"

    def test_ci_none_by_default(self):
        spec = ProjectSpec(name="test")
        assert spec.ci is None

    def test_docker_config(self):
        spec = ProjectSpec(
            name="test",
            docker=DockerConfig(
                include_redis=True,
                include_mcp=True,
                production=DockerProductionConfig(domain="prod.example.com", replicas=3),
            ),
        )
        assert spec.docker is not None
        assert spec.docker.include_redis is True
        assert spec.docker.include_mcp is True
        assert spec.docker.production.domain == "prod.example.com"
        assert spec.docker.production.replicas == 3

    def test_docker_none_by_default(self):
        spec = ProjectSpec(name="test")
        assert spec.docker is None

    def test_deploy_from_dict(self):
        """Test that ProjectSpec accepts deploy as a dict (for TOML/JSON loading)."""
        spec = ProjectSpec(name="test", deploy={"provider": "hetzner", "domain": "example.com"})
        assert spec.deploy is not None
        assert spec.deploy.provider == "hetzner"

    def test_forbids_extra(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectSpec(name="test", unknown="bad")


class TestExposureConfig:
    def test_defaults(self):
        config = ExposureConfig()
        assert config.defaults.default_page_size == 20
        assert config.rest.enabled is True
        assert config.graphql.path == "/graphql"
        assert config.mcp.enabled is True

    def test_graphql_disabled(self):
        from prisme.spec.project import GraphQLConfig

        config = ExposureConfig(graphql=GraphQLConfig(enabled=False))
        assert config.graphql.enabled is False
