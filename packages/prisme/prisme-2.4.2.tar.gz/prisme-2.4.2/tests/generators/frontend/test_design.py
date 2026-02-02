"""Tests for the design system generator.

Tests for:
- ThemeToggle component generation
- Icon component generation
- UI index file generation
- Conditional generation based on config
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.design import DesignSystemGenerator
from prisme.spec.design import DesignSystemConfig
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy, StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def basic_model() -> ModelSpec:
    """Create a basic model for testing."""
    return ModelSpec(
        name="Customer",
        description="Customer entity",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="email", type=FieldType.STRING, required=True),
        ],
    )


@pytest.fixture
def stack_spec_with_default_design(basic_model: ModelSpec) -> StackSpec:
    """Create a stack spec with default design config."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project",
        models=[basic_model],
    )


@pytest.fixture
def stack_spec_with_dark_mode_disabled(basic_model: ModelSpec) -> StackSpec:
    """Create a stack spec with dark mode disabled."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project",
        models=[basic_model],
    )


@pytest.fixture
def stack_spec_with_heroicons(basic_model: ModelSpec) -> StackSpec:
    """Create a stack spec with Heroicons."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project",
        models=[basic_model],
    )


@pytest.fixture
def generator_context_default(
    stack_spec_with_default_design: StackSpec, tmp_path: Path
) -> GeneratorContext:
    """Create a generator context with default design."""
    return GeneratorContext(
        domain_spec=stack_spec_with_default_design,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-project"),
    )


@pytest.fixture
def generator_context_no_dark_mode(
    stack_spec_with_dark_mode_disabled: StackSpec, tmp_path: Path
) -> GeneratorContext:
    """Create a generator context with dark mode disabled."""
    return GeneratorContext(
        domain_spec=stack_spec_with_dark_mode_disabled,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(
            name="test-project",
            design=DesignSystemConfig(dark_mode=False),
        ),
    )


@pytest.fixture
def design_generator_default(generator_context_default: GeneratorContext) -> DesignSystemGenerator:
    """Create a design generator with default config."""
    return DesignSystemGenerator(generator_context_default)


@pytest.fixture
def design_generator_no_dark_mode(
    generator_context_no_dark_mode: GeneratorContext,
) -> DesignSystemGenerator:
    """Create a design generator with dark mode disabled."""
    return DesignSystemGenerator(generator_context_no_dark_mode)


class TestDesignSystemGeneratorFiles:
    """Tests for generated file list."""

    def test_generates_icon_component(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """Generator produces Icon.tsx file."""
        files = design_generator_default.generate_files()
        icon_file = next((f for f in files if "Icon.tsx" in str(f.path)), None)

        assert icon_file is not None
        assert icon_file.path.name == "Icon.tsx"
        assert "ui" in str(icon_file.path)

    def test_generates_theme_toggle_when_dark_mode_enabled(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """Generator produces ThemeToggle.tsx when dark_mode=True."""
        files = design_generator_default.generate_files()
        theme_file = next((f for f in files if "ThemeToggle.tsx" in str(f.path)), None)

        assert theme_file is not None
        assert theme_file.path.name == "ThemeToggle.tsx"

    def test_no_theme_toggle_when_dark_mode_disabled(
        self, design_generator_no_dark_mode: DesignSystemGenerator
    ) -> None:
        """Generator does not produce ThemeToggle.tsx when dark_mode=False."""
        files = design_generator_no_dark_mode.generate_files()
        theme_file = next((f for f in files if "ThemeToggle.tsx" in str(f.path)), None)

        assert theme_file is None

    def test_generates_ui_index(self, design_generator_default: DesignSystemGenerator) -> None:
        """Generator produces ui/index.ts file."""
        files = design_generator_default.generate_files()
        index_file = next((f for f in files if "index.ts" in str(f.path)), None)

        assert index_file is not None
        assert index_file.path.name == "index.ts"
        assert "ui" in str(index_file.path)


class TestDesignSystemGeneratorContent:
    """Tests for generated file content."""

    def test_icon_component_exports_lucide_icons(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """Icon.tsx exports Lucide icons by default."""
        files = design_generator_default.generate_files()
        icon_file = next(f for f in files if "Icon.tsx" in str(f.path))

        assert "lucide-react" in icon_file.content
        assert "Pencil" in icon_file.content
        assert "Trash2" in icon_file.content
        assert "Plus" in icon_file.content

    def test_theme_toggle_imports_lucide_icons(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ThemeToggle.tsx imports Sun and Moon from Lucide."""
        files = design_generator_default.generate_files()
        theme_file = next(f for f in files if "ThemeToggle.tsx" in str(f.path))

        assert "Sun" in theme_file.content
        assert "Moon" in theme_file.content
        assert "lucide-react" in theme_file.content

    def test_theme_toggle_has_local_storage(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ThemeToggle.tsx persists to localStorage."""
        files = design_generator_default.generate_files()
        theme_file = next(f for f in files if "ThemeToggle.tsx" in str(f.path))

        assert "localStorage" in theme_file.content
        assert "prism-theme" in theme_file.content

    def test_theme_toggle_has_system_preference(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ThemeToggle.tsx respects system color scheme preference."""
        files = design_generator_default.generate_files()
        theme_file = next(f for f in files if "ThemeToggle.tsx" in str(f.path))

        assert "prefers-color-scheme" in theme_file.content

    def test_ui_index_exports_icons(self, design_generator_default: DesignSystemGenerator) -> None:
        """ui/index.ts exports Icon component."""
        files = design_generator_default.generate_files()
        index_file = next(f for f in files if "index.ts" in str(f.path))

        assert "export * from './Icon'" in index_file.content

    def test_ui_index_exports_theme_toggle_when_dark_mode_enabled(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ui/index.ts exports ThemeToggle when dark_mode=True."""
        files = design_generator_default.generate_files()
        index_file = next(f for f in files if "index.ts" in str(f.path))

        assert "ThemeToggle" in index_file.content
        assert "useTheme" in index_file.content

    def test_ui_index_no_theme_exports_when_dark_mode_disabled(
        self, design_generator_no_dark_mode: DesignSystemGenerator
    ) -> None:
        """ui/index.ts does not export ThemeToggle when dark_mode=False."""
        files = design_generator_no_dark_mode.generate_files()
        index_file = next(f for f in files if "index.ts" in str(f.path))

        assert "ThemeToggle" not in index_file.content
        assert "useTheme" not in index_file.content


class TestDesignSystemGeneratorStrategy:
    """Tests for file generation strategy."""

    def test_icon_uses_generate_once(self, design_generator_default: DesignSystemGenerator) -> None:
        """Icon.tsx uses GENERATE_ONCE strategy to preserve user customizations."""
        files = design_generator_default.generate_files()
        icon_file = next(f for f in files if "Icon.tsx" in str(f.path))

        assert icon_file.strategy == FileStrategy.GENERATE_ONCE

    def test_theme_toggle_uses_generate_once(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ThemeToggle.tsx uses GENERATE_ONCE strategy to preserve user customizations."""
        files = design_generator_default.generate_files()
        theme_file = next(f for f in files if "ThemeToggle.tsx" in str(f.path))

        assert theme_file.strategy == FileStrategy.GENERATE_ONCE

    def test_ui_index_uses_always_overwrite(
        self, design_generator_default: DesignSystemGenerator
    ) -> None:
        """ui/index.ts uses ALWAYS_OVERWRITE strategy (just exports, safe to regenerate)."""
        files = design_generator_default.generate_files()
        index_file = next(f for f in files if "index.ts" in str(f.path))

        assert index_file.strategy == FileStrategy.ALWAYS_OVERWRITE
