"""CI generator — reads ProjectSpec.ci to generate CI/CD workflows."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase, GeneratorResult


class CIGenerator(GeneratorBase):
    """Generate CI/CD workflows from ProjectSpec.ci."""

    def generate_files(self) -> list[GeneratedFile]:
        return []

    def generate(self) -> GeneratorResult:
        project_spec = self.context.project_spec
        if project_spec is None or project_spec.ci is None:
            return GeneratorResult()

        ci = project_spec.ci

        if ci.provider != "github":
            return GeneratorResult(errors=[f"Unsupported CI provider: {ci.provider}"])

        from prisme.ci import CIConfig as CICLIConfig
        from prisme.ci import GitHubCIGenerator

        config = CICLIConfig(
            project_name=project_spec.name,
            include_frontend=ci.include_frontend,
            use_redis=ci.use_redis,
            enable_codecov=ci.enable_codecov,
            enable_dependabot=ci.enable_dependabot,
            enable_semantic_release=ci.enable_semantic_release,
            enable_commitlint=ci.enable_commitlint,
        )

        project_dir = Path.cwd()
        generator = GitHubCIGenerator(project_dir)
        generator.generate(config)

        return GeneratorResult(written=1)
