"""Tests for template discovery and loading."""

from __future__ import annotations

import pytest

from prisme.utils.template_engine import TemplateRenderer, create_template_environment


def test_create_environment_with_package_loader():
    """Test that template environment can be created with PackageLoader."""
    env = create_template_environment()
    assert env.loader is not None


def test_create_environment_without_package_loader():
    """Test that template environment can be created without PackageLoader."""
    env = create_template_environment(enable_package_loader=False)
    # Should have None loader when no loaders are provided
    assert env.loader is None


def test_template_renderer_initialization():
    """Test that TemplateRenderer initializes correctly."""
    renderer = TemplateRenderer()
    assert renderer.env is not None
    assert renderer.env.loader is not None


def test_get_available_templates():
    """Test listing available templates."""
    renderer = TemplateRenderer()
    templates = renderer.get_available_templates()
    # Currently should be empty list (no templates created yet)
    assert isinstance(templates, list)


def test_get_available_templates_with_prefix():
    """Test listing templates with prefix filter."""
    renderer = TemplateRenderer()
    backend_templates = renderer.get_available_templates(prefix="backend/")
    assert isinstance(backend_templates, list)


def test_validate_templates_exist_with_empty_list():
    """Test validation with empty required templates list."""
    renderer = TemplateRenderer()
    # Should pass with empty list
    assert renderer.validate_templates_exist([]) is True


def test_validate_templates_exist_with_missing_templates():
    """Test validation fails when templates are missing."""
    renderer = TemplateRenderer()
    with pytest.raises(FileNotFoundError, match="Missing required templates"):
        renderer.validate_templates_exist(["nonexistent_template.jinja2"])


def test_validate_templates_exist_no_loader():
    """Test validation fails when no loader is configured."""
    renderer = TemplateRenderer(template_dirs=None)
    renderer.env = create_template_environment(enable_package_loader=False)

    with pytest.raises(FileNotFoundError, match="No template loader configured"):
        renderer.validate_templates_exist(["some_template.jinja2"])


def test_render_string_still_works():
    """Test that render_string method still works (backward compatibility)."""
    renderer = TemplateRenderer()
    template = "Hello {{ name }}!"
    result = renderer.render_string(template, {"name": "World"})
    assert result == "Hello World!"


def test_environment_filters_exist():
    """Test that custom filters are registered."""
    env = create_template_environment()

    # Check case conversion filters
    assert "snake_case" in env.filters
    assert "pascal_case" in env.filters
    assert "camel_case" in env.filters
    assert "kebab_case" in env.filters
    assert "pluralize" in env.filters
    assert "singularize" in env.filters

    # Check utility filters
    assert "indent" in env.filters
    assert "quote" in env.filters
    assert "double_quote" in env.filters
    assert "comment" in env.filters
