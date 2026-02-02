"""Specification loader for Prism.

Provides functions to load and validate StackSpec from Python files.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from prisme.config.schema import PrismeConfig

from pydantic import ValidationError

from prisme.config.loader import load_prisme_config
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec


class _SpecPackageFinder(importlib.abc.MetaPathFinder):
    """Custom import finder for loading sibling modules in spec packages.

    When a spec file uses relative imports like `from .models import user`,
    this finder intercepts the import and loads the module from the spec
    directory.
    """

    def __init__(self, package_name: str, package_path: Path) -> None:
        self.package_name = package_name
        self.package_path = package_path

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        """Find a module spec for imports within our package."""
        # Only handle imports for our specific package
        if not fullname.startswith(self.package_name + "."):
            return None

        # Get the relative module name
        relative_name = fullname[len(self.package_name) + 1 :]

        # Convert to file path (support nested modules like "sub.module")
        parts = relative_name.split(".")
        module_file = self.package_path / "/".join(parts[:-1]) / f"{parts[-1]}.py"

        # Also try as a package
        package_init = self.package_path / "/".join(parts) / "__init__.py"

        if module_file.exists():
            return importlib.util.spec_from_file_location(
                fullname,
                module_file,
                submodule_search_locations=None,
            )
        elif package_init.exists():
            return importlib.util.spec_from_file_location(
                fullname,
                package_init,
                submodule_search_locations=[str(self.package_path / "/".join(parts))],
            )

        return None


class SpecLoadError(Exception):
    """Raised when a specification file cannot be loaded."""

    def __init__(self, message: str, path: Path | None = None) -> None:
        self.path = path
        super().__init__(message)


class SpecValidationError(Exception):
    """Raised when a specification fails validation."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.errors = errors or []
        super().__init__(message)


def load_spec_from_file(path: Path | str) -> StackSpec:
    """Load a StackSpec from a Python file.

    The file should contain either:
    - A `spec` or `stack` variable of type StackSpec
    - A function called `get_spec()` or `create_spec()` that returns a StackSpec

    Supports relative imports within the spec's parent directory (e.g., specs folder).

    Args:
        path: Path to the Python specification file.

    Returns:
        The loaded StackSpec.

    Raises:
        SpecLoadError: If the file cannot be loaded.
        SpecValidationError: If the spec is invalid.
    """
    path = Path(path).resolve()

    if not path.exists():
        raise SpecLoadError(f"Specification file not found: {path}", path)

    if not path.suffix == ".py":
        raise SpecLoadError(f"Specification file must be a Python file: {path}", path)

    # Set up package context to support relative imports
    # The parent directory becomes the package, and the spec file is a module within it
    parent_dir = path.parent
    package_name = f"_prism_specs_{id(path)}"  # Use unique ID to avoid conflicts
    module_name = f"{package_name}.{path.stem}"

    # Add the parent directory to sys.path so sibling modules can be found
    parent_dir_str = str(parent_dir)
    path_added = False
    if parent_dir_str not in sys.path:
        sys.path.insert(0, parent_dir_str)
        path_added = True

    # Install custom import finder for sibling modules
    finder = _SpecPackageFinder(package_name, parent_dir)
    sys.meta_path.insert(0, finder)

    # Track modules we add to clean them up later
    added_modules: list[str] = []

    try:
        # Create a virtual package for the specs directory
        if package_name not in sys.modules:
            package_module = types.ModuleType(package_name)
            package_module.__path__ = [parent_dir_str]
            package_module.__package__ = package_name
            package_module.__file__ = str(parent_dir / "__init__.py")
            sys.modules[package_name] = package_module
            added_modules.append(package_name)

            # Execute __init__.py if it exists
            init_file = parent_dir / "__init__.py"
            if init_file.exists():
                init_spec = importlib.util.spec_from_file_location(
                    package_name,
                    init_file,
                    submodule_search_locations=[parent_dir_str],
                )
                if init_spec is not None and init_spec.loader is not None:
                    try:
                        init_spec.loader.exec_module(package_module)
                    except Exception:
                        pass  # Ignore errors in __init__.py

        # Load the actual spec module
        # Note: Don't pass submodule_search_locations as it creates a namespace package
        # with parent set to the full name, causing __package__ != __spec__.parent
        spec_module_spec = importlib.util.spec_from_file_location(
            module_name,
            path,
        )

        if spec_module_spec is None or spec_module_spec.loader is None:
            raise SpecLoadError(f"Could not load module from: {path}", path)

        module = importlib.util.module_from_spec(spec_module_spec)
        module.__package__ = package_name
        sys.modules[module_name] = module
        added_modules.append(module_name)

        try:
            spec_module_spec.loader.exec_module(module)
        except Exception as e:
            raise SpecLoadError(
                f"Error executing specification file: \n{e}",
                path,
            ) from e

        # Look for the spec
        stack_spec = _find_stack_spec(module, path)

        # Validate the spec
        validate_spec(stack_spec)

        return stack_spec

    finally:
        # Remove our custom finder
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)

        # Clean up sys.path if we added to it
        if path_added and parent_dir_str in sys.path:
            sys.path.remove(parent_dir_str)

        # Clean up any modules we added (including sibling modules loaded via finder)
        modules_to_remove = [name for name in sys.modules if name.startswith(package_name)]
        for mod_name in modules_to_remove:
            del sys.modules[mod_name]


def _find_stack_spec(module: Any, path: Path) -> StackSpec:
    """Find a StackSpec in a loaded module.

    Args:
        module: The loaded module to search.
        path: Path to the module file (for error messages).

    Returns:
        The found StackSpec.

    Raises:
        SpecLoadError: If no StackSpec is found.
    """
    # Check for common variable names
    for name in ("spec", "stack", "stack_spec", "specification"):
        if hasattr(module, name):
            candidate = getattr(module, name)
            if isinstance(candidate, StackSpec):
                return candidate

    # Check for factory functions
    for name in ("get_spec", "create_spec", "get_stack", "create_stack"):
        if hasattr(module, name):
            func = getattr(module, name)
            if callable(func):
                try:
                    candidate = func()
                    if isinstance(candidate, StackSpec):
                        return candidate
                except Exception as e:
                    raise SpecLoadError(
                        f"Error calling {name}(): {e}",
                        path,
                    ) from e

    raise SpecLoadError(
        "No StackSpec found in file. "
        "Define a variable named 'spec' or 'stack', "
        "or a function named 'get_spec()' or 'create_spec()'.",
        path,
    )


def load_spec_from_dict(data: dict[str, Any]) -> StackSpec:
    """Load a StackSpec from a dictionary.

    Args:
        data: Dictionary representation of the spec.

    Returns:
        The loaded StackSpec.

    Raises:
        SpecValidationError: If the spec is invalid.
    """
    try:
        stack_spec = StackSpec.model_validate(data)
    except ValidationError as e:
        raise SpecValidationError(
            f"Invalid specification: {e}",
            errors=e.errors(),  # type: ignore[arg-type]
        ) from e

    validate_spec(stack_spec)
    return stack_spec


def validate_spec(spec: StackSpec) -> None:
    """Validate a StackSpec for consistency.

    Checks for:
    - Duplicate model names
    - Invalid relationship references
    - Invalid foreign key references
    - Circular dependencies

    Args:
        spec: The StackSpec to validate.

    Raises:
        SpecValidationError: If validation fails.
    """
    errors: list[dict[str, Any]] = []
    model_names = {model.name for model in spec.models}

    # Check for duplicate model names
    seen_names: set[str] = set()
    for model in spec.models:
        if model.name in seen_names:
            errors.append(
                {
                    "type": "duplicate_model",
                    "msg": f"Duplicate model name: {model.name}",
                    "model": model.name,
                    "fix": f"Rename one of the '{model.name}' models to a unique name.",
                }
            )
        seen_names.add(model.name)

    # Check each model
    for model in spec.models:
        # Check field names are unique within model
        field_names: set[str] = set()
        for field in model.fields:
            if field.name in field_names:
                errors.append(
                    {
                        "type": "duplicate_field",
                        "msg": f"Duplicate field name in {model.name}: {field.name}",
                        "model": model.name,
                        "field": field.name,
                        "fix": f"Rename the duplicate '{field.name}' field in {model.name}.",
                    }
                )
            field_names.add(field.name)

            # Check foreign key references
            if field.references and field.references not in model_names:
                available = ", ".join(sorted(model_names))
                errors.append(
                    {
                        "type": "invalid_reference",
                        "msg": f"Foreign key in {model.name}.{field.name} "
                        f"references unknown model: {field.references}",
                        "model": model.name,
                        "field": field.name,
                        "reference": field.references,
                        "fix": f"Change references='{field.references}' to one of: {available}",
                    }
                )

        # Check relationship references
        for rel in model.relationships:
            if rel.target_model not in model_names:
                available = ", ".join(sorted(model_names))
                errors.append(
                    {
                        "type": "invalid_relationship",
                        "msg": f"Relationship {model.name}.{rel.name} "
                        f"references unknown model: {rel.target_model}",
                        "model": model.name,
                        "relationship": rel.name,
                        "target": rel.target_model,
                        "fix": f"Change target_model='{rel.target_model}' to one of: {available}",
                    }
                )

    if errors:
        raise SpecValidationError(
            f"Specification validation failed with {len(errors)} error(s)",
            errors=errors,
        )


def get_model_dependency_order(spec: StackSpec) -> list[str]:
    """Get models in dependency order (models without dependencies first).

    Args:
        spec: The StackSpec to analyze.

    Returns:
        List of model names in dependency order.
    """
    # Build dependency graph
    dependencies: dict[str, set[str]] = {}
    for model in spec.models:
        deps: set[str] = set()
        for field in model.fields:
            if field.references:
                deps.add(field.references)
        # Don't include self-references
        deps.discard(model.name)
        dependencies[model.name] = deps

    # Topological sort
    result: list[str] = []
    remaining = set(dependencies.keys())

    while remaining:
        # Find models with no remaining dependencies
        ready = {name for name in remaining if not dependencies[name].intersection(remaining)}

        if not ready:
            # Circular dependency - just pick one
            ready = {next(iter(remaining))}

        result.extend(sorted(ready))
        remaining -= ready

    return result


def load_domain_spec(path: Path | str) -> StackSpec:
    """Load a domain spec (StackSpec) from a Python file.

    Alias for load_spec_from_file with clearer v2 naming.

    Args:
        path: Path to the domain spec Python file.

    Returns:
        The loaded StackSpec.
    """
    return load_spec_from_file(path)


def load_project_spec(path: Path | str) -> ProjectSpec:
    """Load a ProjectSpec from a Python file.

    The file should contain a `project` or `project_spec` variable of type ProjectSpec,
    or a function `get_project()` / `create_project()` that returns one.

    Args:
        path: Path to the project spec Python file.

    Returns:
        The loaded ProjectSpec.

    Raises:
        SpecLoadError: If the file cannot be loaded or no ProjectSpec is found.
    """
    path = Path(path).resolve()

    if not path.exists():
        raise SpecLoadError(f"Project spec file not found: {path}", path)

    if not path.suffix == ".py":
        raise SpecLoadError(f"Project spec file must be a Python file: {path}", path)

    import importlib.util

    module_name = f"_prisme_project_{id(path)}"

    spec_module_spec = importlib.util.spec_from_file_location(module_name, path)
    if spec_module_spec is None or spec_module_spec.loader is None:
        raise SpecLoadError(f"Could not load module from: {path}", path)

    module = importlib.util.module_from_spec(spec_module_spec)
    sys.modules[module_name] = module

    try:
        spec_module_spec.loader.exec_module(module)
    except Exception as e:
        raise SpecLoadError(
            f"Error executing project spec file: \n{e}",
            path,
        ) from e
    finally:
        sys.modules.pop(module_name, None)

    # Look for ProjectSpec
    for name in ("project", "project_spec", "spec"):
        if hasattr(module, name):
            candidate = getattr(module, name)
            if isinstance(candidate, ProjectSpec):
                return candidate

    for name in ("get_project", "create_project"):
        if hasattr(module, name):
            func = getattr(module, name)
            if callable(func):
                try:
                    candidate = func()
                    if isinstance(candidate, ProjectSpec):
                        return candidate
                except Exception as e:
                    raise SpecLoadError(f"Error calling {name}(): {e}", path) from e

    raise SpecLoadError(
        "No ProjectSpec found in file. "
        "Define a variable named 'project' or 'project_spec', "
        "or a function named 'get_project()' or 'create_project()'.",
        path,
    )


def load_config(path: Path | str) -> PrismeConfig:
    """Load PrismeConfig from a TOML file.

    Convenience wrapper around config.loader.load_prisme_config.

    Args:
        path: Path to prisme.toml.

    Returns:
        The loaded PrismeConfig.
    """
    return load_prisme_config(path)


__all__ = [
    "SpecLoadError",
    "SpecValidationError",
    "get_model_dependency_order",
    "load_config",
    "load_domain_spec",
    "load_project_spec",
    "load_spec_from_dict",
    "load_spec_from_file",
    "validate_spec",
]
