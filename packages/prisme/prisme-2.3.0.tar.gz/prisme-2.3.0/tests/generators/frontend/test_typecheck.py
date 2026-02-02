"""Tests that frontend generators produce valid TypeScript.

Each test runs a generator, then invokes `npx tsc --noEmit` to verify
the output is free of type errors.

Marked @pytest.mark.slow because they require npm install + tsc.
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend import (
    ComponentsGenerator,
    DesignSystemGenerator,
    FrontendAuthGenerator,
    GraphQLOpsGenerator,
    HeadlessGenerator,
    HooksGenerator,
    PagesGenerator,
    RouterGenerator,
    TypeScriptGenerator,
    WidgetSystemGenerator,
)
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import GeneratorConfig, ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


def _make_package_json() -> dict:
    """Minimal package.json for type-checking generated code."""
    return {
        "name": "prism-typecheck-test",
        "private": True,
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.20.0",
            "@apollo/client": "^3.8.0",
            "graphql": "^16.8.0",
        },
        "devDependencies": {
            "typescript": "^5.3.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
        },
    }


def _make_tsconfig() -> dict:
    """Minimal tsconfig.json for type-checking generated code."""
    return {
        "compilerOptions": {
            "target": "ES2020",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "jsx": "react-jsx",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "noEmit": True,
            "baseUrl": ".",
            "paths": {"@/*": ["src/*"]},
        },
        "include": ["src"],
    }


@pytest.mark.slow
class TestFrontendTypechecks:
    """Verify each frontend generator produces valid TypeScript."""

    @pytest.fixture(scope="class")
    def frontend_project(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Set up a minimal React+TS project with dependencies installed."""
        root = tmp_path_factory.mktemp("frontend")
        (root / "src").mkdir()

        (root / "package.json").write_text(json.dumps(_make_package_json(), indent=2))
        (root / "tsconfig.json").write_text(json.dumps(_make_tsconfig(), indent=2))

        result = subprocess.run(
            ["npm", "install", "--ignore-scripts"],
            cwd=root,
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"npm install failed: {result.stderr.decode()}")

        return root

    @pytest.fixture
    def stack_spec(self) -> StackSpec:
        """Create a representative stack spec."""
        return StackSpec(
            name="test-project",
            version="1.0.0",
            description="Test project",
            models=[
                ModelSpec(
                    name="Customer",
                    description="Customer entity",
                    timestamps=True,
                    fields=[
                        FieldSpec(name="name", type=FieldType.STRING, required=True),
                        FieldSpec(name="email", type=FieldType.STRING, required=True),
                        FieldSpec(name="age", type=FieldType.INTEGER, required=False),
                        FieldSpec(name="is_active", type=FieldType.BOOLEAN, required=False),
                    ],
                ),
            ],
        )

    @pytest.fixture
    def generator_context(self, frontend_project: Path, stack_spec: StackSpec) -> GeneratorContext:
        """Create a GeneratorContext pointing at the frontend project."""
        # The generators write to output_dir / <frontend_output> / ...
        # We need output_dir such that frontend_output resolves to frontend_project/src
        # Default frontend_output is "packages/frontend/src"
        # So set output_dir to a parent that makes it work, OR override the spec.
        # Easiest: override generator config so frontend_output points at our tmp dir.
        project = ProjectSpec(
            name="test-project",
            generator=GeneratorConfig(frontend_output="src"),
        )
        return GeneratorContext(
            domain_spec=stack_spec,
            output_dir=frontend_project,
            project_spec=project,
        )

    def _run_tsc(self, frontend_project: Path) -> subprocess.CompletedProcess:
        """Run tsc --noEmit and return the result."""
        return subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=frontend_project,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_typescript_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        gen = TypeScriptGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_graphql_ops_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        # GraphQL ops depends on types
        TypeScriptGenerator(generator_context).generate()
        gen = GraphQLOpsGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_headless_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        gen = HeadlessGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_design_system_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        gen = DesignSystemGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_widget_system_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        gen = WidgetSystemGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_components_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        gen = ComponentsGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_hooks_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        gen = HooksGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_pages_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        ComponentsGenerator(generator_context).generate()
        gen = PagesGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_router_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        PagesGenerator(generator_context).generate()
        gen = RouterGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"

    def test_frontend_auth_generator(
        self, generator_context: GeneratorContext, frontend_project: Path
    ) -> None:
        TypeScriptGenerator(generator_context).generate()
        gen = FrontendAuthGenerator(generator_context)
        gen.generate()
        result = self._run_tsc(frontend_project)
        assert result.returncode == 0, f"tsc failed:\n{result.stdout}\n{result.stderr}"
