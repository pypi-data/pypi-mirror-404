"""Tests for deployment configuration models."""

from prisme.deploy.config import (
    DeploymentConfig,
    HetznerConfig,
    HetznerLocation,
    HetznerServerType,
)


class TestHetznerServerType:
    """Tests for HetznerServerType enum."""

    def test_server_types_have_correct_values(self) -> None:
        """Test that server types have correct string values."""
        assert HetznerServerType.CX22.value == "cx22"
        assert HetznerServerType.CX32.value == "cx32"
        assert HetznerServerType.CX42.value == "cx42"
        assert HetznerServerType.CX52.value == "cx52"
        assert HetznerServerType.CAX11.value == "cax11"


class TestHetznerLocation:
    """Tests for HetznerLocation enum."""

    def test_locations_have_correct_values(self) -> None:
        """Test that locations have correct string values."""
        assert HetznerLocation.NUREMBERG.value == "nbg1"
        assert HetznerLocation.FALKENSTEIN.value == "fsn1"
        assert HetznerLocation.HELSINKI.value == "hel1"
        assert HetznerLocation.ASHBURN.value == "ash"
        assert HetznerLocation.HILLSBORO.value == "hil"


class TestHetznerConfig:
    """Tests for HetznerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that HetznerConfig has sensible defaults."""
        config = HetznerConfig()

        assert config.location == HetznerLocation.FALKENSTEIN
        assert config.staging_server_type == HetznerServerType.CX23
        assert config.production_server_type == HetznerServerType.CX23
        assert config.staging_volume_size == 10
        assert config.production_volume_size == 20
        assert config.production_floating_ip is True
        assert config.private_network_ip_range == "10.0.0.0/16"
        assert config.network_zone == "eu-central"

    def test_custom_values(self) -> None:
        """Test that HetznerConfig accepts custom values."""
        config = HetznerConfig(
            location=HetznerLocation.HELSINKI,
            staging_server_type=HetznerServerType.CX32,
            production_server_type=HetznerServerType.CX42,
            staging_volume_size=20,
            production_volume_size=50,
            production_floating_ip=False,
        )

        assert config.location == HetznerLocation.HELSINKI
        assert config.staging_server_type == HetznerServerType.CX32
        assert config.production_server_type == HetznerServerType.CX42
        assert config.staging_volume_size == 20
        assert config.production_volume_size == 50
        assert config.production_floating_ip is False

    def test_default_firewall_rules(self) -> None:
        """Test that default firewall rules are created."""
        config = HetznerConfig()

        assert len(config.firewall_rules) == 3
        ports = [rule["port"] for rule in config.firewall_rules]
        assert 22 in ports  # SSH
        assert 80 in ports  # HTTP
        assert 443 in ports  # HTTPS


class TestDeploymentConfig:
    """Tests for DeploymentConfig dataclass."""

    def test_required_project_name(self) -> None:
        """Test that project_name is required."""
        config = DeploymentConfig(project_name="myapp")
        assert config.project_name == "myapp"

    def test_default_values(self) -> None:
        """Test that DeploymentConfig has sensible defaults."""
        config = DeploymentConfig(project_name="myapp")

        assert config.domain == ""
        assert config.ssl_email == ""
        assert config.use_redis is False
        assert config.postgres_version == "16"
        assert config.postgres_user == "app"
        assert config.enable_swap is True
        assert config.swap_size_mb == 1024
        assert config.docker_registry == "ghcr.io"

    def test_postgres_db_defaults_to_project_name(self) -> None:
        """Test that postgres_db defaults to project_name."""
        config = DeploymentConfig(project_name="myapp")
        assert config.postgres_db == "myapp"

    def test_postgres_db_converts_hyphens_to_underscores(self) -> None:
        """Test that hyphens in project name are converted for postgres_db."""
        config = DeploymentConfig(project_name="my-cool-app")
        assert config.postgres_db == "my_cool_app"

    def test_custom_postgres_db_preserved(self) -> None:
        """Test that custom postgres_db is preserved."""
        config = DeploymentConfig(project_name="myapp", postgres_db="custom_db")
        assert config.postgres_db == "custom_db"

    def test_nested_hetzner_config(self) -> None:
        """Test that nested HetznerConfig works correctly."""
        hetzner = HetznerConfig(
            location=HetznerLocation.ASHBURN,
            staging_server_type=HetznerServerType.CX32,
        )
        config = DeploymentConfig(project_name="myapp", hetzner=hetzner)

        assert config.hetzner.location == HetznerLocation.ASHBURN
        assert config.hetzner.staging_server_type == HetznerServerType.CX32

    def test_full_configuration(self) -> None:
        """Test a fully configured DeploymentConfig."""
        hetzner = HetznerConfig(
            location=HetznerLocation.HELSINKI,
            production_floating_ip=True,
        )
        config = DeploymentConfig(
            project_name="production-app",
            domain="example.com",
            ssl_email="admin@example.com",
            use_redis=True,
            hetzner=hetzner,
            postgres_user="produser",
            postgres_db="proddb",
            enable_swap=False,
        )

        assert config.project_name == "production-app"
        assert config.domain == "example.com"
        assert config.ssl_email == "admin@example.com"
        assert config.use_redis is True
        assert config.hetzner.location == HetznerLocation.HELSINKI
        assert config.postgres_user == "produser"
        assert config.postgres_db == "proddb"
        assert config.enable_swap is False
