"""Docker generator — reads ProjectSpec.docker to generate Docker config."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase, GeneratorResult


class DockerGenerator(GeneratorBase):
    """Generate Docker configuration from ProjectSpec.docker."""

    def generate_files(self) -> list[GeneratedFile]:
        return []

    def generate(self) -> GeneratorResult:
        project_spec = self.context.project_spec
        if project_spec is None or project_spec.docker is None:
            return GeneratorResult()

        docker = project_spec.docker
        written = 0

        from prisme.docker import ComposeConfig, ComposeGenerator

        gen_config = project_spec.generator
        backend_output = Path(gen_config.backend_output)
        frontend_output = Path(gen_config.frontend_output)

        project_dir = Path.cwd()

        backend_path_relative = str(backend_output.parent)
        frontend_path_relative = str(
            frontend_output.parent
            if (project_dir / frontend_output.parent / "package.json").exists()
            else frontend_output
        )
        backend_module = project_spec.backend.module_name or backend_output.name

        config = ComposeConfig(
            project_name=project_spec.name.replace("-", "_"),
            backend_path=backend_path_relative,
            frontend_path=frontend_path_relative,
            backend_module=backend_module,
            use_redis=docker.include_redis,
            use_mcp=docker.include_mcp,
            mcp_path=gen_config.mcp_path,
        )

        generator = ComposeGenerator(project_dir)
        generator.generate(config)
        written += 1

        # Generate production config if domain or non-default replicas are set
        prod = docker.production
        if prod.domain or prod.replicas != 2:
            from prisme.docker import ProductionComposeGenerator, ProductionConfig

            prod_config = ProductionConfig(
                project_name=project_spec.name,
                use_redis=docker.include_redis,
                domain=prod.domain,
                backend_replicas=prod.replicas,
            )

            prod_generator = ProductionComposeGenerator(project_dir)
            prod_generator.generate(prod_config)
            written += 1

        return GeneratorResult(written=written)
