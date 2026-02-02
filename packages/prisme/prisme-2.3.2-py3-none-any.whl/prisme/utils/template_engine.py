"""Jinja2 template engine wrapper with Prism-specific filters.

Provides a configured Jinja2 environment with custom filters for
code generation tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PackageLoader, StrictUndefined

from prisme.utils.case_conversion import (
    pluralize,
    singularize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


def create_template_environment(
    template_dirs: list[Path] | None = None,
    enable_package_loader: bool = True,
) -> Environment:
    """Create a configured Jinja2 environment.

    Args:
        template_dirs: Optional list of directories to search for templates.
        enable_package_loader: Whether to enable loading templates from the installed package.

    Returns:
        Configured Jinja2 Environment.
    """
    from jinja2 import BaseLoader

    loaders: list[BaseLoader] = []

    # Add package templates (from installed prism package)
    if enable_package_loader:
        loaders.append(PackageLoader("prisme", "templates/jinja2"))

    # Add user-provided directories (for custom templates)
    if template_dirs:
        loaders.extend(FileSystemLoader(str(d)) for d in template_dirs)

    env = Environment(
        loader=ChoiceLoader(loaders) if loaders else None,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Add case conversion filters
    env.filters["snake_case"] = to_snake_case
    env.filters["pascal_case"] = to_pascal_case
    env.filters["camel_case"] = to_camel_case
    env.filters["kebab_case"] = to_kebab_case
    env.filters["pluralize"] = pluralize
    env.filters["singularize"] = singularize

    # Add utility filters
    env.filters["indent"] = indent_filter
    env.filters["quote"] = quote_filter
    env.filters["double_quote"] = double_quote_filter
    env.filters["comment"] = comment_filter

    return env


def indent_filter(text: str, width: int = 4, first: bool = False) -> str:
    """Indent text by a given number of spaces.

    Args:
        text: The text to indent.
        width: Number of spaces to indent.
        first: Whether to indent the first line.

    Returns:
        Indented text.
    """
    indent = " " * width
    lines = text.split("\n")

    if first:
        return "\n".join(indent + line if line else line for line in lines)
    else:
        result = [lines[0]] if lines else []
        result.extend(indent + line if line else line for line in lines[1:])
        return "\n".join(result)


def quote_filter(text: str) -> str:
    """Wrap text in single quotes.

    Args:
        text: The text to quote.

    Returns:
        Quoted text.
    """
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def double_quote_filter(text: str) -> str:
    """Wrap text in double quotes.

    Args:
        text: The text to quote.

    Returns:
        Double-quoted text.
    """
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def comment_filter(text: str, style: str = "python") -> str:
    """Convert text to a comment.

    Args:
        text: The text to comment.
        style: Comment style ('python', 'js', 'sql').

    Returns:
        Commented text.
    """
    lines = text.split("\n")

    if style == "python":
        return "\n".join(f"# {line}" if line.strip() else "#" for line in lines)
    elif style in ("js", "javascript", "typescript"):
        return "\n".join(f"// {line}" if line.strip() else "//" for line in lines)
    elif style == "sql":
        return "\n".join(f"-- {line}" if line.strip() else "--" for line in lines)
    else:
        return "\n".join(f"# {line}" if line.strip() else "#" for line in lines)


def render_template_string(
    template_string: str,
    context: dict[str, Any],
) -> str:
    """Render a template string with the given context.

    Args:
        template_string: The Jinja2 template string.
        context: Template variables.

    Returns:
        Rendered string.
    """
    env = create_template_environment()
    template = env.from_string(template_string)
    return template.render(**context)


class TemplateRenderer:
    """Template renderer for code generation."""

    def __init__(self, template_dirs: list[Path] | None = None) -> None:
        """Initialize the template renderer.

        Args:
            template_dirs: Directories to search for templates.
        """
        self.env = create_template_environment(template_dirs)
        self._string_templates: dict[str, Any] = {}

    def render_string(
        self,
        template_string: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template string.

        Args:
            template_string: The template string to render.
            context: Template variables.

        Returns:
            Rendered string.
        """
        # Cache compiled templates for reuse
        if template_string not in self._string_templates:
            self._string_templates[template_string] = self.env.from_string(template_string)

        return self._string_templates[template_string].render(**context)

    def render_file(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template file.

        Args:
            template_name: Name of the template file.
            context: Template variables.

        Returns:
            Rendered string.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def get_available_templates(self, prefix: str = "") -> list[str]:
        """List all available templates matching a prefix.

        Args:
            prefix: Optional prefix to filter templates (e.g., "backend/models/").

        Returns:
            List of template names matching the prefix.
        """
        if self.env.loader is None:
            return []

        all_templates = self.env.list_templates()
        if prefix:
            return [t for t in all_templates if t.startswith(prefix)]
        return list(all_templates)

    def validate_templates_exist(self, required_templates: list[str]) -> bool:
        """Verify all required templates are available.

        Args:
            required_templates: List of template names that must exist.

        Returns:
            True if all templates exist.

        Raises:
            FileNotFoundError: If any required template is missing.
        """
        if self.env.loader is None:
            raise FileNotFoundError("No template loader configured")

        available = set(self.env.list_templates())
        missing = set(required_templates) - available

        if missing:
            missing_list = ", ".join(sorted(missing))
            raise FileNotFoundError(f"Missing required templates: {missing_list}")

        return True


# Common code generation templates
# These constants load from external template files for backward compatibility


def _load_header_template(template_name: str) -> str:
    """Load a header template from the package templates directory.

    Args:
        template_name: Name of the template file (e.g., 'python_file.jinja2')

    Returns:
        Template content as a string
    """
    template_path = (
        Path(__file__).parent.parent / "templates" / "jinja2" / "common" / "headers" / template_name
    )
    return template_path.read_text()


PYTHON_FILE_HEADER = _load_header_template("python_file.jinja2")

PYTHON_GENERATED_HEADER = _load_header_template("python_generated.jinja2")

PYTHON_EXTENSION_HEADER = _load_header_template("python_extension.jinja2")

TYPESCRIPT_GENERATED_HEADER = _load_header_template("typescript_generated.jinja2")

TYPESCRIPT_EXTENSION_HEADER = _load_header_template("typescript_extension.jinja2")


__all__ = [
    "PYTHON_EXTENSION_HEADER",
    "PYTHON_FILE_HEADER",
    "PYTHON_GENERATED_HEADER",
    "TYPESCRIPT_EXTENSION_HEADER",
    "TYPESCRIPT_GENERATED_HEADER",
    "TemplateRenderer",
    "comment_filter",
    "create_template_environment",
    "double_quote_filter",
    "indent_filter",
    "quote_filter",
    "render_template_string",
]
