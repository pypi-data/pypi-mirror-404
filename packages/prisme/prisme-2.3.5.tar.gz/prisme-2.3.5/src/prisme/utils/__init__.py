"""Prism utilities.

This module contains utility functions for:
- String case conversion (snake_case, PascalCase, etc.)
- File handling with protected regions
- Template rendering
- Specification loading and validation
"""

from prisme.utils.case_conversion import (
    pluralize,
    singularize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)
from prisme.utils.file_handler import (
    ParsedFile,
    ProtectedRegion,
    ensure_directory,
    get_relative_import,
    merge_protected_regions,
    parse_protected_regions,
    should_write_file,
    write_file_with_strategy,
)
from prisme.utils.spec_loader import (
    SpecLoadError,
    SpecValidationError,
    get_model_dependency_order,
    load_spec_from_dict,
    load_spec_from_file,
    validate_spec,
)
from prisme.utils.template_engine import (
    PYTHON_EXTENSION_HEADER,
    PYTHON_FILE_HEADER,
    PYTHON_GENERATED_HEADER,
    TYPESCRIPT_EXTENSION_HEADER,
    TYPESCRIPT_GENERATED_HEADER,
    TemplateRenderer,
    create_template_environment,
    render_template_string,
)

__all__ = [
    # Template engine
    "PYTHON_EXTENSION_HEADER",
    "PYTHON_FILE_HEADER",
    "PYTHON_GENERATED_HEADER",
    "TYPESCRIPT_EXTENSION_HEADER",
    "TYPESCRIPT_GENERATED_HEADER",
    # File handling
    "ParsedFile",
    "ProtectedRegion",
    # Spec loading
    "SpecLoadError",
    "SpecValidationError",
    "TemplateRenderer",
    "create_template_environment",
    "ensure_directory",
    "get_model_dependency_order",
    "get_relative_import",
    "load_spec_from_dict",
    "load_spec_from_file",
    "merge_protected_regions",
    "parse_protected_regions",
    # Case conversion
    "pluralize",
    "render_template_string",
    "should_write_file",
    "singularize",
    "to_camel_case",
    "to_kebab_case",
    "to_pascal_case",
    "to_snake_case",
    "validate_spec",
    "write_file_with_strategy",
]
