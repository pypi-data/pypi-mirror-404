"""Widget system generator for Prism.

Generates the pluggable widget system for frontend forms including:
- Widget types and interfaces
- Default widget mapping
- Widget registry
- React context provider
- Default widget components
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class WidgetSystemGenerator(GeneratorBase):
    """Generator for the widget system."""

    REQUIRED_TEMPLATES = [
        "frontend/widgets/types.ts.jinja2",
        "frontend/widgets/defaults.ts.jinja2",
        "frontend/widgets/registry.ts.jinja2",
        "frontend/widgets/context.tsx.jinja2",
        "frontend/widgets/setup.ts.jinja2",
        "frontend/widgets/components/TextInput.tsx.jinja2",
        "frontend/widgets/components/TextArea.tsx.jinja2",
        "frontend/widgets/components/NumberInput.tsx.jinja2",
        "frontend/widgets/components/Checkbox.tsx.jinja2",
        "frontend/widgets/components/Select.tsx.jinja2",
        "frontend/widgets/components/DatePicker.tsx.jinja2",
        "frontend/widgets/components/EmailInput.tsx.jinja2",
        "frontend/widgets/components/UrlInput.tsx.jinja2",
        "frontend/widgets/components/PhoneInput.tsx.jinja2",
        "frontend/widgets/components/PasswordInput.tsx.jinja2",
        "frontend/widgets/components/CurrencyInput.tsx.jinja2",
        "frontend/widgets/components/PercentageInput.tsx.jinja2",
        "frontend/widgets/components/TagInput.tsx.jinja2",
        "frontend/widgets/components/JsonEditor.tsx.jinja2",
        "frontend/widgets/components/RelationSelect.tsx.jinja2",
        "frontend/widgets/components/index.ts.jinja2",
        "frontend/widgets/index.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.prism_path = frontend_base / self.generator_config.prism_path
        self.widgets_path = self.prism_path / "widgets"

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all widget system files."""
        return [
            self._generate_types(),
            self._generate_defaults(),
            self._generate_registry(),
            self._generate_context(),
            self._generate_setup(),
            # Default widget components
            self._generate_text_input(),
            self._generate_textarea(),
            self._generate_number_input(),
            self._generate_checkbox(),
            self._generate_select(),
            self._generate_date_picker(),
            # Extended widget components
            self._generate_email_input(),
            self._generate_url_input(),
            self._generate_phone_input(),
            self._generate_password_input(),
            self._generate_currency_input(),
            self._generate_percentage_input(),
            self._generate_tag_input(),
            self._generate_json_editor(),
            self._generate_relation_select(),
            self._generate_components_index(),
            self._generate_widgets_index(),
        ]

    def _generate_types(self) -> GeneratedFile:
        """Generate widget type definitions."""
        content = self.renderer.render_file(
            "frontend/widgets/types.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "types.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Widget types",
        )

    def _generate_defaults(self) -> GeneratedFile:
        """Generate default widget mapping."""
        content = self.renderer.render_file(
            "frontend/widgets/defaults.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "defaults.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Default widget mapping",
        )

    def _generate_registry(self) -> GeneratedFile:
        """Generate widget registry class."""
        content = self.renderer.render_file(
            "frontend/widgets/registry.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "registry.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Widget registry",
        )

    def _generate_context(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/context.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "context.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Widget context",
        )

    def _generate_setup(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/setup.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.prism_path / "setup.ts",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description="Widget setup",
        )

    def _generate_text_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/TextInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "TextInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="TextInput widget",
        )

    def _generate_textarea(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/TextArea.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "TextArea.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="TextArea widget",
        )

    def _generate_number_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/NumberInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "NumberInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="NumberInput widget",
        )

    def _generate_checkbox(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/Checkbox.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "Checkbox.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Checkbox widget",
        )

    def _generate_select(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/Select.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "Select.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Select widget",
        )

    def _generate_date_picker(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/DatePicker.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "DatePicker.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="DatePicker widget",
        )

    def _generate_email_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/EmailInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "EmailInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="EmailInput widget",
        )

    def _generate_url_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/UrlInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "UrlInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="UrlInput widget",
        )

    def _generate_phone_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/PhoneInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "PhoneInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="PhoneInput widget",
        )

    def _generate_password_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/PasswordInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "PasswordInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="PasswordInput widget",
        )

    def _generate_currency_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/CurrencyInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "CurrencyInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="CurrencyInput widget",
        )

    def _generate_percentage_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/PercentageInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "PercentageInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="PercentageInput widget",
        )

    def _generate_tag_input(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/TagInput.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "TagInput.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="TagInput widget",
        )

    def _generate_json_editor(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/JsonEditor.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "JsonEditor.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="JsonEditor widget",
        )

    def _generate_relation_select(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/RelationSelect.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "RelationSelect.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="RelationSelect widget",
        )

    def _generate_components_index(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/components/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "components" / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Widget components index",
        )

    def _generate_widgets_index(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "frontend/widgets/index.ts.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.widgets_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Widgets module index",
        )


__all__ = ["WidgetSystemGenerator"]
