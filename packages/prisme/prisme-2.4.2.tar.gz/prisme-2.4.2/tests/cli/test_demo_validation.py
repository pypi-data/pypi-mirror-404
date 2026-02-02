"""Tests for validating the demo specification.

These tests validate the demo spec file (specs/demo.py) using the CLI commands,
simulating the one-liner validation approach:
    prism validate specs/demo.py
    prism generate specs/demo.py --dry-run

This ensures the demo spec is always valid and can be used for documentation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner

# Get the project root directory (where specs/demo.py lives)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEMO_SPEC_PATH = PROJECT_ROOT / "specs" / "demo.py"


class TestDemoSpecExists:
    """Tests that the demo spec file exists and is accessible."""

    def test_demo_spec_file_exists(self) -> None:
        """Demo spec file exists at specs/demo.py."""
        assert DEMO_SPEC_PATH.exists(), f"Demo spec not found at {DEMO_SPEC_PATH}"

    def test_demo_spec_is_file(self) -> None:
        """Demo spec path is a file, not a directory."""
        assert DEMO_SPEC_PATH.is_file()

    def test_demo_spec_is_readable(self) -> None:
        """Demo spec file is readable."""
        content = DEMO_SPEC_PATH.read_text()
        assert len(content) > 0


class TestDemoSpecValidation:
    """Tests for validating the demo spec with prism validate."""

    def test_validate_demo_spec_succeeds(self, cli_runner: CliRunner) -> None:
        """prism validate specs/demo.py succeeds."""
        result = cli_runner.invoke(main, ["validate", str(DEMO_SPEC_PATH)])

        assert result.exit_code == 0, f"Validation failed: {result.output}"
        assert "valid" in result.output.lower()

    def test_validate_shows_demo_spec_name(self, cli_runner: CliRunner) -> None:
        """Validation output includes the demo spec name."""
        result = cli_runner.invoke(main, ["validate", str(DEMO_SPEC_PATH)])

        assert result.exit_code == 0
        assert "prism-demo" in result.output

    def test_validate_shows_all_models(self, cli_runner: CliRunner) -> None:
        """Validation output lists all demo models."""
        result = cli_runner.invoke(main, ["validate", str(DEMO_SPEC_PATH)])

        assert result.exit_code == 0
        # Check for expected models from the demo spec
        assert "Company" in result.output
        assert "Employee" in result.output
        assert "Project" in result.output
        assert "Task" in result.output
        assert "StockPrice" in result.output
        assert "Document" in result.output
        assert "AuditLog" in result.output


class TestDemoSpecGeneration:
    """Tests for generating code from the demo spec."""

    def test_generate_warns_without_config_or_spec(self, cli_runner: CliRunner) -> None:
        """prism generate shows warning when prisme.toml is missing and no spec provided."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["generate"])

            assert result.exit_code == 1
            assert "prisme.toml" in result.output
            assert "prisme create" in result.output
            assert "--force" in result.output

    def test_generate_dry_run_succeeds(self, cli_runner: CliRunner) -> None:
        """prism generate specs/demo.py --dry-run succeeds."""
        result = cli_runner.invoke(main, ["generate", str(DEMO_SPEC_PATH), "--dry-run"])

        assert result.exit_code == 0, f"Generation failed: {result.output}"
        assert "dry run" in result.output.lower()

    def test_generate_shows_summary(self, cli_runner: CliRunner) -> None:
        """Generation output shows file summary."""
        result = cli_runner.invoke(main, ["generate", str(DEMO_SPEC_PATH), "--dry-run"])

        assert result.exit_code == 0
        # Should show some indication of what would be generated
        assert (
            "Summary" in result.output
            or "Total" in result.output
            or "files" in result.output.lower()
        )

    def test_generate_with_only_option(self, cli_runner: CliRunner) -> None:
        """prism generate with --only option works."""
        result = cli_runner.invoke(
            main, ["generate", str(DEMO_SPEC_PATH), "--dry-run", "--only", "models"]
        )

        # Should not fail
        assert result.exit_code == 0 or "error" not in result.output.lower()


class TestDemoSpecContent:
    """Tests for the content of the demo spec file."""

    def test_demo_spec_has_stack_variable(self) -> None:
        """Demo spec defines a stack variable."""
        content = DEMO_SPEC_PATH.read_text()
        assert "stack = StackSpec(" in content

    def test_demo_spec_has_docstring(self) -> None:
        """Demo spec has a module docstring."""
        content = DEMO_SPEC_PATH.read_text()
        assert content.startswith('"""')

    def test_demo_spec_documents_features(self) -> None:
        """Demo spec docstring documents demonstrated features."""
        content = DEMO_SPEC_PATH.read_text()

        # Check for feature documentation in docstring
        assert "field types" in content.lower() or "FieldType" in content
        assert "filter operators" in content.lower() or "FilterOperator" in content
        assert "relationships" in content.lower() or "RelationshipSpec" in content
        assert "nested" in content.lower() or "nested_create" in content
        assert "temporal" in content.lower() or "TemporalConfig" in content

    def test_demo_spec_has_exports(self) -> None:
        """Demo spec exports the stack variable."""
        content = DEMO_SPEC_PATH.read_text()
        assert "__all__" in content
        assert '"stack"' in content or "'stack'" in content


class TestDemoSpecImports:
    """Tests that the demo spec has all necessary imports."""

    def test_demo_spec_imports_all_field_types(self) -> None:
        """Demo spec imports FieldType."""
        content = DEMO_SPEC_PATH.read_text()
        assert "FieldType" in content

    def test_demo_spec_imports_filter_operators(self) -> None:
        """Demo spec imports FilterOperator."""
        content = DEMO_SPEC_PATH.read_text()
        assert "FilterOperator" in content

    def test_demo_spec_imports_v2_overrides(self) -> None:
        """Demo spec imports v2 override types."""
        content = DEMO_SPEC_PATH.read_text()
        assert "DeliveryOverrides" in content
        assert "FrontendOverrides" in content
        assert "MCPOverrides" in content

    def test_demo_spec_imports_core(self) -> None:
        """Demo spec imports core specification classes."""
        content = DEMO_SPEC_PATH.read_text()
        assert "StackSpec" in content
        assert "ModelSpec" in content
        assert "FieldSpec" in content
        assert "FieldType" in content


class TestDemoSpecLoadable:
    """Tests that the demo spec can be loaded as a Python module."""

    def test_demo_spec_is_valid_python(self) -> None:
        """Demo spec is valid Python syntax."""
        import ast

        content = DEMO_SPEC_PATH.read_text()
        # Should not raise SyntaxError
        ast.parse(content)

    def test_demo_spec_can_be_imported(self) -> None:
        """Demo spec can be loaded with the spec loader."""
        from prisme.utils.spec_loader import load_spec_from_file

        # Should not raise any errors
        spec = load_spec_from_file(DEMO_SPEC_PATH)
        assert spec is not None
        assert spec.name == "prism-demo"

    def test_demo_spec_has_expected_model_count(self) -> None:
        """Demo spec has the expected number of models."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        # Should have 7 models: Company, Employee, Project, Task, StockPrice, Document, AuditLog
        assert len(spec.models) == 7

    def test_demo_spec_models_have_valid_fields(self) -> None:
        """All demo models have at least one field."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        for model in spec.models:
            assert len(model.fields) > 0, f"Model {model.name} has no fields"


class TestDemoSpecFeatures:
    """Tests that demo spec showcases all major features."""

    def test_demo_has_soft_delete_model(self) -> None:
        """Demo spec includes models with soft_delete."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        soft_delete_models = [m for m in spec.models if m.soft_delete]
        assert len(soft_delete_models) > 0, "No models with soft_delete=True"

    def test_demo_has_timestamp_model(self) -> None:
        """Demo spec includes models with timestamps."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        timestamp_models = [m for m in spec.models if m.timestamps]
        assert len(timestamp_models) > 0, "No models with timestamps=True"

    def test_demo_has_nested_create(self) -> None:
        """Demo spec includes model with nested_create."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        nested_create_models = [m for m in spec.models if m.nested_create]
        assert len(nested_create_models) > 0, "No models with nested_create"

    def test_demo_has_temporal_model(self) -> None:
        """Demo spec includes model with temporal config."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        temporal_models = [m for m in spec.models if m.temporal]
        assert len(temporal_models) > 0, "No models with temporal config"

    def test_demo_has_relationships(self) -> None:
        """Demo spec includes models with relationships."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        models_with_relationships = [m for m in spec.models if m.relationships]
        assert len(models_with_relationships) > 0, "No models with relationships"

    def test_demo_has_foreign_key_fields(self) -> None:
        """Demo spec includes foreign key fields."""
        from prisme.spec.fields import FieldType
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        fk_fields = []
        for model in spec.models:
            fk_fields.extend([f for f in model.fields if f.type == FieldType.FOREIGN_KEY])

        assert len(fk_fields) > 0, "No foreign key fields"

    def test_demo_has_enum_fields(self) -> None:
        """Demo spec includes enum fields."""
        from prisme.spec.fields import FieldType
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        enum_fields = []
        for model in spec.models:
            enum_fields.extend([f for f in model.fields if f.type == FieldType.ENUM])

        assert len(enum_fields) > 0, "No enum fields"

    def test_demo_has_json_fields(self) -> None:
        """Demo spec includes JSON fields."""
        from prisme.spec.fields import FieldType
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        json_fields = []
        for model in spec.models:
            json_fields.extend([f for f in model.fields if f.type == FieldType.JSON])

        assert len(json_fields) > 0, "No JSON fields"

    def test_demo_has_typed_json_fields(self) -> None:
        """Demo spec includes typed JSON array fields."""
        from prisme.spec.fields import FieldType
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        typed_json_fields = []
        for model in spec.models:
            for field in model.fields:
                if field.type == FieldType.JSON and field.json_item_type:
                    typed_json_fields.append(field)

        assert len(typed_json_fields) > 0, "No typed JSON array fields"

    def test_demo_has_custom_widgets(self) -> None:
        """Demo spec includes fields with custom ui_widget."""
        from prisme.utils.spec_loader import load_spec_from_file

        spec = load_spec_from_file(DEMO_SPEC_PATH)

        widget_fields = []
        for model in spec.models:
            widget_fields.extend([f for f in model.fields if f.ui_widget])

        assert len(widget_fields) > 0, "No fields with custom ui_widget"


class TestDemoSpecOneLiner:
    """Tests simulating the one-liner validation approach."""

    def test_full_validation_pipeline(self, cli_runner: CliRunner) -> None:
        """
        Simulate the validation part of the one-liner:
        prism validate && prism generate --dry-run

        This tests:
        1. Spec loads correctly
        2. Spec validates successfully
        3. Spec can be used for generation (dry-run)
        """
        # Step 1: Validate
        validate_result = cli_runner.invoke(main, ["validate", str(DEMO_SPEC_PATH)])
        assert validate_result.exit_code == 0, f"Validation failed: {validate_result.output}"

        # Step 2: Generate (dry-run)
        generate_result = cli_runner.invoke(main, ["generate", str(DEMO_SPEC_PATH), "--dry-run"])
        assert generate_result.exit_code == 0, f"Generation failed: {generate_result.output}"
