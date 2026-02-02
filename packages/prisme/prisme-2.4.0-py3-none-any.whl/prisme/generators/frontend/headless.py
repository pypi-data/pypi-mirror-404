"""Headless UI hooks generator for Prism.

Generates model-agnostic composable primitives and UI state hooks
that sit between the API/data hooks and visual components. This gives
developers composable primitives for building custom UIs without
reimplementing common patterns like pagination, selection, sorting,
modals, and toasts.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class HeadlessGenerator(GeneratorBase):
    """Generator for headless UI hooks and composables.

    Generates model-agnostic primitives in the prism/headless/ directory:
    - Composables: usePagination, useSelection, useSorting, useFiltering, useSearch
    - UI State: useModal, useConfirmation, useToast, useDrawer
    - Utilities: transform, export
    """

    REQUIRED_TEMPLATES = [
        # Types
        "frontend/headless/types.ts.jinja2",
        # Composables
        "frontend/headless/composables/usePagination.ts.jinja2",
        "frontend/headless/composables/useSelection.ts.jinja2",
        "frontend/headless/composables/useSorting.ts.jinja2",
        "frontend/headless/composables/useFiltering.ts.jinja2",
        "frontend/headless/composables/useSearch.ts.jinja2",
        "frontend/headless/composables/index.ts.jinja2",
        # UI State
        "frontend/headless/ui/useModal.ts.jinja2",
        "frontend/headless/ui/useConfirmation.tsx.jinja2",
        "frontend/headless/ui/useToast.tsx.jinja2",
        "frontend/headless/ui/useDrawer.ts.jinja2",
        "frontend/headless/ui/index.ts.jinja2",
        # Utilities
        "frontend/headless/utils/transform.ts.jinja2",
        "frontend/headless/utils/export.ts.jinja2",
        "frontend/headless/utils/index.ts.jinja2",
        # Index
        "frontend/headless/index.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.prism_path = frontend_base / self.generator_config.prism_path
        self.headless_path = self.prism_path / "headless"

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all headless UI files."""
        return [
            # Types
            self._generate_types(),
            # Composables
            self._generate_use_pagination(),
            self._generate_use_selection(),
            self._generate_use_sorting(),
            self._generate_use_filtering(),
            self._generate_use_search(),
            self._generate_composables_index(),
            # UI State
            self._generate_use_modal(),
            self._generate_use_confirmation(),
            self._generate_use_toast(),
            self._generate_use_drawer(),
            self._generate_ui_index(),
            # Utilities
            self._generate_transform(),
            self._generate_export(),
            self._generate_utils_index(),
            # Main index
            self._generate_headless_index(),
        ]

    def _generate_types(self) -> GeneratedFile:
        """Generate headless types definitions."""
        content = self.renderer.render_file(
            "frontend/headless/types.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "types.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Headless types",
        )

    # Composable hooks

    def _generate_use_pagination(self) -> GeneratedFile:
        """Generate usePagination hook."""
        content = self.renderer.render_file(
            "frontend/headless/composables/usePagination.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "usePagination.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="usePagination hook",
        )

    def _generate_use_selection(self) -> GeneratedFile:
        """Generate useSelection hook."""
        content = self.renderer.render_file(
            "frontend/headless/composables/useSelection.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "useSelection.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useSelection hook",
        )

    def _generate_use_sorting(self) -> GeneratedFile:
        """Generate useSorting hook."""
        content = self.renderer.render_file(
            "frontend/headless/composables/useSorting.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "useSorting.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useSorting hook",
        )

    def _generate_use_filtering(self) -> GeneratedFile:
        """Generate useFiltering hook."""
        content = self.renderer.render_file(
            "frontend/headless/composables/useFiltering.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "useFiltering.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useFiltering hook",
        )

    def _generate_use_search(self) -> GeneratedFile:
        """Generate useSearch hook."""
        content = self.renderer.render_file(
            "frontend/headless/composables/useSearch.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "useSearch.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useSearch hook",
        )

    def _generate_composables_index(self) -> GeneratedFile:
        """Generate composables index."""
        content = self.renderer.render_file(
            "frontend/headless/composables/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "composables" / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Composables index",
        )

    # UI State hooks

    def _generate_use_modal(self) -> GeneratedFile:
        """Generate useModal hook."""
        content = self.renderer.render_file(
            "frontend/headless/ui/useModal.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "ui" / "useModal.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useModal hook",
        )

    def _generate_use_confirmation(self) -> GeneratedFile:
        """Generate useConfirmation hook with context provider."""
        content = self.renderer.render_file(
            "frontend/headless/ui/useConfirmation.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "ui" / "useConfirmation.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useConfirmation hook",
        )

    def _generate_use_toast(self) -> GeneratedFile:
        """Generate useToast hook with context provider."""
        content = self.renderer.render_file(
            "frontend/headless/ui/useToast.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "ui" / "useToast.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useToast hook",
        )

    def _generate_use_drawer(self) -> GeneratedFile:
        """Generate useDrawer hook."""
        content = self.renderer.render_file(
            "frontend/headless/ui/useDrawer.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "ui" / "useDrawer.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="useDrawer hook",
        )

    def _generate_ui_index(self) -> GeneratedFile:
        """Generate UI index."""
        content = self.renderer.render_file(
            "frontend/headless/ui/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "ui" / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="UI hooks index",
        )

    # Utilities

    def _generate_transform(self) -> GeneratedFile:
        """Generate transform utilities."""
        content = self.renderer.render_file(
            "frontend/headless/utils/transform.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "utils" / "transform.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Transform utilities",
        )

    def _generate_export(self) -> GeneratedFile:
        """Generate export utilities."""
        content = self.renderer.render_file(
            "frontend/headless/utils/export.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "utils" / "export.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Export utilities",
        )

    def _generate_utils_index(self) -> GeneratedFile:
        """Generate utils index."""
        content = self.renderer.render_file(
            "frontend/headless/utils/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "utils" / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Utils index",
        )

    def _generate_headless_index(self) -> GeneratedFile:
        """Generate main headless index."""
        content = self.renderer.render_file(
            "frontend/headless/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.headless_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Headless module index",
        )


__all__ = ["HeadlessGenerator"]
