"""Deploy generator — reads ProjectSpec.deploy to generate deployment infra."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase, GeneratorResult


class DeployGenerator(GeneratorBase):
    """Generate deployment infrastructure from ProjectSpec.deploy."""

    def generate_files(self) -> list[GeneratedFile]:
        # Not used — we override generate() to delegate to existing generator.
        return []

    def generate(self) -> GeneratorResult:
        project_spec = self.context.project_spec
        if project_spec is None or project_spec.deploy is None:
            return GeneratorResult()

        deploy = project_spec.deploy

        if deploy.provider != "hetzner":
            return GeneratorResult(errors=[f"Unsupported deploy provider: {deploy.provider}"])

        from prisme.deploy import DeploymentConfig, HetznerConfig, HetznerDeployGenerator
        from prisme.deploy.config import HetznerLocation, HetznerServerType

        hetzner = deploy.hetzner

        location_map = {
            "nbg1": HetznerLocation.NUREMBERG,
            "fsn1": HetznerLocation.FALKENSTEIN,
            "hel1": HetznerLocation.HELSINKI,
            "ash": HetznerLocation.ASHBURN,
            "hil": HetznerLocation.HILLSBORO,
        }
        server_type_map = {
            "cx22": HetznerServerType.CX22,
            "cx23": HetznerServerType.CX23,
            "cx32": HetznerServerType.CX32,
            "cx42": HetznerServerType.CX42,
            "cx52": HetznerServerType.CX52,
            "cax11": HetznerServerType.CAX11,
        }

        hetzner_config = HetznerConfig(
            location=location_map.get(hetzner.location, HetznerLocation.FALKENSTEIN),
            staging_server_type=server_type_map.get(
                hetzner.staging_server_type, HetznerServerType.CX23
            ),
            production_server_type=server_type_map.get(
                hetzner.production_server_type, HetznerServerType.CX23
            ),
            production_floating_ip=hetzner.production_floating_ip,
        )

        config = DeploymentConfig(
            project_name=project_spec.name,
            domain=deploy.domain,
            ssl_email=deploy.ssl_email,
            use_redis=deploy.use_redis,
            hetzner=hetzner_config,
        )

        project_dir = Path.cwd()
        generator = HetznerDeployGenerator(project_dir, config)
        generator.generate()

        return GeneratorResult(written=1)
