"""Tests for the widget system generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.widgets import WidgetSystemGenerator
from prisme.spec.project import ProjectSpec

if TYPE_CHECKING:
    from pathlib import Path

    from prisme.spec.stack import StackSpec


@pytest.fixture
def generator_context(sample_stack_spec: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create a generator context for testing."""
    return GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-project"),
    )


@pytest.fixture
def widget_generator(generator_context: GeneratorContext) -> WidgetSystemGenerator:
    """Create a widget system generator for testing."""
    return WidgetSystemGenerator(generator_context)


class TestWidgetSystemGenerator:
    """Tests for WidgetSystemGenerator."""

    def test_generate_files_returns_all_widgets(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """Generator produces all expected widget files."""
        files = widget_generator.generate_files()

        # Get all file paths
        file_paths = [str(f.path) for f in files]

        # Check core widget files
        assert any("types.ts" in p for p in file_paths)
        assert any("defaults.ts" in p for p in file_paths)
        assert any("registry.ts" in p for p in file_paths)
        assert any("context.tsx" in p for p in file_paths)
        assert any("setup.ts" in p for p in file_paths)

        # Check basic widget components
        assert any("TextInput.tsx" in p for p in file_paths)
        assert any("TextArea.tsx" in p for p in file_paths)
        assert any("NumberInput.tsx" in p for p in file_paths)
        assert any("Checkbox.tsx" in p for p in file_paths)
        assert any("Select.tsx" in p for p in file_paths)
        assert any("DatePicker.tsx" in p for p in file_paths)

        # Check extended widget components
        assert any("EmailInput.tsx" in p for p in file_paths)
        assert any("UrlInput.tsx" in p for p in file_paths)
        assert any("PhoneInput.tsx" in p for p in file_paths)
        assert any("PasswordInput.tsx" in p for p in file_paths)
        assert any("CurrencyInput.tsx" in p for p in file_paths)
        assert any("PercentageInput.tsx" in p for p in file_paths)
        assert any("TagInput.tsx" in p for p in file_paths)
        assert any("JsonEditor.tsx" in p for p in file_paths)
        assert any("RelationSelect.tsx" in p for p in file_paths)

    def test_generate_files_count(self, widget_generator: WidgetSystemGenerator) -> None:
        """Generator produces expected number of files."""
        files = widget_generator.generate_files()

        # 5 system files + 6 basic widgets + 9 extended widgets + 2 index files = 22
        assert len(files) == 22

    def test_defaults_includes_extended_widgets(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """Generated defaults.ts includes extended widget imports and mappings."""
        files = widget_generator.generate_files()
        defaults_file = next(f for f in files if "defaults.ts" in str(f.path))

        content = defaults_file.content

        # Check imports
        assert "EmailInput" in content
        assert "UrlInput" in content
        assert "PhoneInput" in content
        assert "PasswordInput" in content
        assert "CurrencyInput" in content
        assert "PercentageInput" in content
        assert "TagInput" in content
        assert "JsonEditor" in content
        assert "RelationSelect" in content

        # Check UI_WIDGET_MAP entries
        assert "email: EmailInput" in content
        assert "url: UrlInput" in content
        assert "phone: PhoneInput" in content
        assert "password: PasswordInput" in content
        assert "currency: CurrencyInput" in content
        assert "percentage: PercentageInput" in content
        assert "tags: TagInput" in content
        assert "json: JsonEditor" in content
        assert "relation: RelationSelect" in content

    def test_default_widgets_uses_json_editor(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """DEFAULT_WIDGETS maps json type to JsonEditor."""
        files = widget_generator.generate_files()
        defaults_file = next(f for f in files if "defaults.ts" in str(f.path))

        content = defaults_file.content
        assert "json: JsonEditor" in content

    def test_default_widgets_uses_relation_select(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """DEFAULT_WIDGETS maps foreign_key type to RelationSelect."""
        files = widget_generator.generate_files()
        defaults_file = next(f for f in files if "defaults.ts" in str(f.path))

        content = defaults_file.content
        assert "foreign_key: RelationSelect" in content

    def test_components_index_exports_all_widgets(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """Components index exports all widget components."""
        files = widget_generator.generate_files()
        index_file = next(
            f for f in files if "components" in str(f.path) and "index.ts" in str(f.path)
        )

        content = index_file.content

        # Check core exports
        assert "export { TextInput }" in content
        assert "export { TextArea }" in content
        assert "export { NumberInput }" in content
        assert "export { Checkbox }" in content
        assert "export { Select }" in content
        assert "export { DatePicker }" in content

        # Check extended exports
        assert "export { EmailInput }" in content
        assert "export { UrlInput }" in content
        assert "export { PhoneInput }" in content
        assert "export { PasswordInput }" in content
        assert "export { CurrencyInput }" in content
        assert "export { PercentageInput }" in content
        assert "export { TagInput }" in content
        assert "export { JsonEditor }" in content
        assert "export { RelationSelect }" in content


class TestEmailInputWidget:
    """Tests for EmailInput widget generation."""

    def test_email_input_uses_email_type(self, widget_generator: WidgetSystemGenerator) -> None:
        """EmailInput uses type='email' for browser validation."""
        files = widget_generator.generate_files()
        email_file = next(f for f in files if "EmailInput.tsx" in str(f.path))

        content = email_file.content
        assert 'type="email"' in content
        assert 'autoComplete="email"' in content


class TestPasswordInputWidget:
    """Tests for PasswordInput widget generation."""

    def test_password_input_has_show_hide_toggle(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """PasswordInput includes show/hide toggle functionality."""
        files = widget_generator.generate_files()
        password_file = next(f for f in files if "PasswordInput.tsx" in str(f.path))

        content = password_file.content
        assert "showPassword" in content
        assert "setShowPassword" in content

    def test_password_input_has_strength_indicator(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """PasswordInput includes password strength indicator."""
        files = widget_generator.generate_files()
        password_file = next(f for f in files if "PasswordInput.tsx" in str(f.path))

        content = password_file.content
        assert "getPasswordStrength" in content
        assert "showStrength" in content


class TestCurrencyInputWidget:
    """Tests for CurrencyInput widget generation."""

    def test_currency_input_has_locale_support(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """CurrencyInput supports locale and currency formatting."""
        files = widget_generator.generate_files()
        currency_file = next(f for f in files if "CurrencyInput.tsx" in str(f.path))

        content = currency_file.content
        assert "currency" in content
        assert "locale" in content
        assert "Intl.NumberFormat" in content


class TestTagInputWidget:
    """Tests for TagInput widget generation."""

    def test_tag_input_handles_string_array(self, widget_generator: WidgetSystemGenerator) -> None:
        """TagInput is designed for string array values."""
        files = widget_generator.generate_files()
        tag_file = next(f for f in files if "TagInput.tsx" in str(f.path))

        content = tag_file.content
        assert "WidgetBaseProps<string[]>" in content
        assert "maxTags" in content


class TestJsonEditorWidget:
    """Tests for JsonEditor widget generation."""

    def test_json_editor_has_format_button(self, widget_generator: WidgetSystemGenerator) -> None:
        """JsonEditor includes JSON formatting functionality."""
        files = widget_generator.generate_files()
        json_file = next(f for f in files if "JsonEditor.tsx" in str(f.path))

        content = json_file.content
        assert "formatJson" in content
        assert "JSON.stringify" in content
        assert "JSON.parse" in content


class TestRelationSelectWidget:
    """Tests for RelationSelect widget generation."""

    def test_relation_select_supports_async_loading(
        self, widget_generator: WidgetSystemGenerator
    ) -> None:
        """RelationSelect supports async option loading."""
        files = widget_generator.generate_files()
        relation_file = next(f for f in files if "RelationSelect.tsx" in str(f.path))

        content = relation_file.content
        assert "loadOptions" in content
        assert "isLoading" in content

    def test_relation_select_is_searchable(self, widget_generator: WidgetSystemGenerator) -> None:
        """RelationSelect includes search functionality."""
        files = widget_generator.generate_files()
        relation_file = next(f for f in files if "RelationSelect.tsx" in str(f.path))

        content = relation_file.content
        assert "searchable" in content
        assert "searchTerm" in content
