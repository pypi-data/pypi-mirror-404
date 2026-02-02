"""Tests for the router generator.

Regression tests for:
- Issue: Router generates routes for pages that don't exist
- Issue: Nav links generated despite include_in_nav=False
- Issue: Custom routes not preserved in router.tsx
- Issue: App.tsx overwrites custom providers on regeneration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.router import RouterGenerator
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.overrides import FrontendOverrides
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy, StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def model_with_no_form_or_detail() -> ModelSpec:
    """Create a model with generate_form=False and generate_detail_view=False."""
    return ModelSpec(
        name="WindRoseSector",
        description="Wind rose sector data (internal model)",
        fields=[
            FieldSpec(name="direction", type=FieldType.INTEGER, required=True),
            FieldSpec(name="frequency", type=FieldType.FLOAT, required=True),
        ],
        expose=True,
        operations=["create", "read", "update", "delete", "list"],
        frontend_overrides=FrontendOverrides(
            include_in_nav=False,
            generate_form=False,
            generate_table=True,
            generate_detail_view=False,
        ),
    )


@pytest.fixture
def model_with_full_frontend() -> ModelSpec:
    """Create a model with full frontend generation."""
    return ModelSpec(
        name="Customer",
        description="Customer entity",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="email", type=FieldType.STRING, required=True),
        ],
        expose=True,
        frontend_overrides=FrontendOverrides(
            include_in_nav=True,
            generate_form=True,
            generate_table=True,
            generate_detail_view=True,
        ),
    )


@pytest.fixture
def stack_spec_with_mixed_models(
    model_with_no_form_or_detail: ModelSpec,
    model_with_full_frontend: ModelSpec,
) -> StackSpec:
    """Create a stack spec with models having different frontend settings."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project for router generation",
        models=[model_with_no_form_or_detail, model_with_full_frontend],
    )


@pytest.fixture
def generator_context(stack_spec_with_mixed_models: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create a generator context for testing."""
    return GeneratorContext(
        domain_spec=stack_spec_with_mixed_models,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-project"),
    )


@pytest.fixture
def router_generator(generator_context: GeneratorContext) -> RouterGenerator:
    """Create a router generator for testing."""
    return RouterGenerator(generator_context)


class TestRouterGeneratorFrontendExposure:
    """Tests that router respects FrontendExposure settings.

    Regression tests for issue: Router generates routes for pages that don't exist.
    """

    def test_no_detail_import_when_generate_detail_view_false(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should not import detail page when generate_detail_view=False."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # WindRoseSector has generate_detail_view=False, so detail import should not exist
        assert "WindRoseSectorDetailPage" not in content
        assert "wind-rose-sectors/[id]'" not in content

    def test_no_form_imports_when_generate_form_false(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should not import create/edit pages when generate_form=False."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # WindRoseSector has generate_form=False, so create/edit imports should not exist
        assert "WindRoseSectorCreatePage" not in content
        assert "WindRoseSectorEditPage" not in content
        assert "wind-rose-sectors/new'" not in content
        assert "wind-rose-sectors/[id]/edit'" not in content

    def test_list_import_still_generated(self, router_generator: RouterGenerator) -> None:
        """Router should still import list page (generate_table=True)."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # WindRoseSector has generate_table=True, so list import should exist
        assert "WindRoseSectorsListPage" in content
        assert "/wind-rose-sectors'" in content

    def test_full_frontend_model_has_all_routes(self, router_generator: RouterGenerator) -> None:
        """Model with full frontend should have all routes generated."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # Customer has all frontend flags true, should have all imports
        assert "CustomersListPage" in content
        assert "CustomerDetailPage" in content
        assert "CustomerCreatePage" in content
        assert "CustomerEditPage" in content


class TestRouterGeneratorNavigation:
    """Tests that router respects include_in_nav setting.

    Regression tests for issue: Nav links generated despite include_in_nav=False.
    """

    def test_no_nav_link_when_include_in_nav_false(self, router_generator: RouterGenerator) -> None:
        """Router should not generate nav link when include_in_nav=False."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # WindRoseSector has include_in_nav=False, should not be in nav
        # Check for NavLink with the route path
        assert 'to="/wind-rose-sectors"' not in content

    def test_nav_link_generated_when_include_in_nav_true(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should generate nav link when include_in_nav=True."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        # Customer has include_in_nav=True, should be in nav
        assert 'to="/customers"' in content
        assert "Customers" in content


class TestRouterGeneratorProtectedRegions:
    """Tests that router uses ALWAYS_OVERWRITE strategy with protected regions.

    Regression tests for issue: Custom routes not preserved in router.tsx.
    """

    def test_router_uses_always_overwrite_strategy(self, router_generator: RouterGenerator) -> None:
        """Router file should use ALWAYS_OVERWRITE strategy."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))

        assert router_file.strategy == FileStrategy.ALWAYS_OVERWRITE

    def test_router_has_custom_imports_protected_region(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should have protected region for custom imports."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        assert "PRISM:PROTECTED:START - Custom Imports" in content
        assert "PRISM:PROTECTED:END" in content

    def test_router_has_custom_routes_protected_region(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should have protected region for custom routes."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        assert "PRISM:PROTECTED:START - Custom Routes" in content

    def test_router_has_custom_nav_links_protected_region(
        self, router_generator: RouterGenerator
    ) -> None:
        """Router should have protected region for custom nav links."""
        files = router_generator.generate_files()
        router_file = next(f for f in files if "router.tsx" in str(f.path))
        content = router_file.content

        assert "PRISM:PROTECTED:START - Custom Nav Links" in content


class TestAppGeneratorProtectedRegions:
    """Tests that App.tsx uses ALWAYS_OVERWRITE strategy with protected regions.

    Regression tests for issue: App.tsx overwrites custom providers on regeneration.
    """

    def test_app_uses_always_overwrite_strategy(self, router_generator: RouterGenerator) -> None:
        """App.tsx file should use ALWAYS_OVERWRITE strategy."""
        files = router_generator.generate_files()
        app_file = next(f for f in files if "App.tsx" in str(f.path))

        assert app_file.strategy == FileStrategy.ALWAYS_OVERWRITE

    def test_app_has_custom_imports_protected_region(
        self, router_generator: RouterGenerator
    ) -> None:
        """App.tsx should have protected region for custom imports."""
        files = router_generator.generate_files()
        app_file = next(f for f in files if "App.tsx" in str(f.path))
        content = app_file.content

        assert "PRISM:PROTECTED:START - Custom Imports" in content
        assert "PRISM:PROTECTED:END" in content

    def test_app_has_custom_providers_protected_region(
        self, router_generator: RouterGenerator
    ) -> None:
        """App.tsx should have protected region for custom providers."""
        files = router_generator.generate_files()
        app_file = next(f for f in files if "App.tsx" in str(f.path))
        content = app_file.content

        assert "PRISM:PROTECTED:START - Custom Providers" in content
