"""Base classes for Prism code generators.

Provides the foundational infrastructure for all code generators,
including file handling, template rendering, and strategy support.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prisme.spec.stack import FileStrategy, StackSpec
from prisme.tracking.logger import OverrideLogger
from prisme.tracking.manifest import (
    ManifestManager,
    TrackedFile,
    hash_content,
)
from prisme.utils.file_handler import (
    write_file_with_strategy,
)
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.config.schema import PrismeConfig
    from prisme.spec.model import ModelSpec
    from prisme.spec.project import ProjectSpec


@dataclass
class GeneratedFile:
    """Represents a file to be generated.

    Attributes:
        path: The relative path for the file (relative to output directory).
        content: The file content.
        strategy: How to handle existing files.
        description: Optional description for logging.
        has_hooks: Whether the file includes hook methods for customization.
        extends: Path to base file if this is an extension file.
    """

    path: Path
    content: str
    strategy: FileStrategy = FileStrategy.ALWAYS_OVERWRITE
    description: str = ""
    has_hooks: bool = False
    extends: Path | None = None

    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = Path(self.path)
        if isinstance(self.extends, str):
            self.extends = Path(self.extends)


@dataclass
class GeneratorContext:
    """Context passed to generators during code generation.

    Context passed to generators during code generation.

    Attributes:
        domain_spec: The domain specification (models, fields, relationships).
        output_dir: The base output directory.
        dry_run: If True, don't write files.
        force: If True, overwrite all files regardless of strategy.
        protected_marker: Marker string for protected regions.
        backend_module_name: Optional override for backend Python module name.
        project_spec: The project specification (infrastructure config, optional).
        config: The prisme.toml configuration (optional).
        spec: Deprecated alias for domain_spec.
    """

    domain_spec: StackSpec
    output_dir: Path
    dry_run: bool = False
    force: bool = False
    protected_marker: str = "PRISM:PROTECTED"
    backend_module_name: str | None = None
    project_spec: ProjectSpec | None = None
    config: PrismeConfig | None = None

    @property
    def spec(self) -> StackSpec:
        """Deprecated v1 alias for domain_spec."""
        return self.domain_spec


@dataclass
class GeneratorResult:
    """Result of running a generator.

    Attributes:
        files: List of files that were generated.
        written: Number of files actually written.
        skipped: Number of files skipped (due to strategy).
        errors: List of error messages.
    """

    files: list[GeneratedFile] = field(default_factory=list)
    written: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Whether generation was successful (no errors)."""
        return len(self.errors) == 0


class GeneratorBase(ABC):
    """Base class for all code generators.

    Subclasses should implement the `generate_files` method to produce
    a list of GeneratedFile objects.

    Example:
        >>> class MyGenerator(GeneratorBase):
        ...     def generate_files(self) -> list[GeneratedFile]:
        ...         return [
        ...             GeneratedFile(
        ...                 path=Path("output.py"),
        ...                 content="# Generated code",
        ...                 strategy=FileStrategy.ALWAYS_OVERWRITE,
        ...             )
        ...         ]
    """

    def __init__(self, context: GeneratorContext) -> None:
        """Initialize the generator.

        Args:
            context: The generator context with spec and settings.
        """
        self.context = context
        self.spec = context.domain_spec
        self.output_dir = context.output_dir
        self.renderer = TemplateRenderer()

    @property
    def project_spec(self) -> ProjectSpec | None:
        """Get the project spec if available."""
        return self.context.project_spec

    @property
    def generator_config(self) -> Any:
        """Get generator config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.generator
        msg = "project_spec is required for generator_config"
        raise ValueError(msg)

    @property
    def exposure_config(self) -> Any:
        """Get exposure config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.exposure
        return None

    @property
    def auth_config(self) -> Any:
        """Get auth config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.auth
        msg = "project_spec is required for auth_config"
        raise ValueError(msg)

    @property
    def design_config(self) -> Any:
        """Get design config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.design
        msg = "project_spec is required for design_config"
        raise ValueError(msg)

    @property
    def testing_config(self) -> Any:
        """Get testing config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.testing
        msg = "project_spec is required for testing_config"
        raise ValueError(msg)

    @property
    def database_config(self) -> Any:
        """Get database config from project_spec."""
        if self.context.project_spec:
            return self.context.project_spec.database
        msg = "project_spec is required for database_config"
        raise ValueError(msg)

    def get_package_name(self) -> str:
        """Get the backend Python package/module name.

        Uses backend_module_name from config if set,
        otherwise falls back to snake_case of spec name.
        """
        from prisme.utils.case_conversion import to_snake_case

        if self.context.backend_module_name:
            return self.context.backend_module_name
        return to_snake_case(self.spec.name)

    @abstractmethod
    def generate_files(self) -> list[GeneratedFile]:
        """Generate the list of files.

        Subclasses must implement this method to return the files
        to be generated.

        Returns:
            List of GeneratedFile objects.
        """
        ...

    @property
    def _generation_mode(self) -> str:
        """Get the generation mode (strict or lenient) from config."""
        if self.context.config:
            return self.context.config.generation.mode
        return "lenient"

    def generate(self) -> GeneratorResult:
        """Run the generator and write files.

        In strict mode, any warnings are promoted to errors and generation
        fails. In lenient mode (the default), warnings are collected but
        generation proceeds.

        Returns:
            GeneratorResult with statistics and any errors.
        """
        result = GeneratorResult()
        self._current_warnings: list[str] = []

        try:
            files = self.generate_files()
            result.files = files
        except Exception as e:
            result.errors.append(f"Generation failed: {e}")
            return result

        for generated_file in files:
            try:
                written = self._write_file(generated_file)
                if written:
                    result.written += 1
                else:
                    result.skipped += 1
            except Exception as e:
                result.errors.append(f"Error writing {generated_file.path}: {e}")

        result.warnings = self._current_warnings

        # In strict mode, promote warnings to errors
        if self._generation_mode == "strict" and result.warnings:
            result.errors.extend(f"[strict] {w}" for w in result.warnings)

        return result

    def _write_file(self, generated_file: GeneratedFile) -> bool:
        """Write a single generated file with tracking.

        Args:
            generated_file: The file to write.

        Returns:
            True if the file was written, False if skipped.
        """
        full_path = self.output_dir / generated_file.path

        # Load manifest to check for user modifications
        manifest = ManifestManager.load(self.output_dir)

        # Check if file exists and user has modified it
        user_modified = False
        if full_path.exists():
            current_content = full_path.read_text()
            user_modified = manifest.is_modified(str(generated_file.path), current_content)

        # Override strategy if force is set
        strategy = generated_file.strategy
        if self.context.force:
            strategy = FileStrategy.ALWAYS_OVERWRITE

        # If user modified and strategy respects user changes, skip writing
        if user_modified and strategy != FileStrategy.ALWAYS_OVERWRITE:
            # Log the override for user review (unless in dry_run mode)
            if not self.context.dry_run:
                OverrideLogger.log_override(
                    path=full_path,
                    generated_content=generated_file.content,
                    user_content=current_content,
                    strategy=strategy,
                    project_dir=self.output_dir,
                )
            return False  # Don't overwrite user's version

        # Warn when overwriting manually edited ALWAYS_OVERWRITE files
        if user_modified and strategy == FileStrategy.ALWAYS_OVERWRITE:
            from rich.console import Console

            Console(stderr=True).print(
                f"[yellow]\u26a0 {generated_file.path} was manually edited — overwriting[/]"
            )
            # Collect as warning for strict mode enforcement
            self._current_warnings.append(
                f"{generated_file.path} was manually edited — overwriting"
            )

        # Write file normally
        written = write_file_with_strategy(
            path=full_path,
            content=generated_file.content,
            strategy=strategy,
            marker=self.context.protected_marker,
            dry_run=self.context.dry_run,
        )

        # Track in manifest if written (and not in dry_run mode)
        if written and not self.context.dry_run:
            manifest.track_file(
                TrackedFile(
                    path=str(generated_file.path),
                    strategy=strategy.value,
                    content_hash=hash_content(generated_file.content),
                    generated_at=datetime.now().isoformat(),
                    has_hooks=generated_file.has_hooks,
                    extends=str(generated_file.extends) if generated_file.extends else None,
                )
            )
            ManifestManager.save(manifest, self.output_dir)

        return written

    def render(self, template: str, **context: Any) -> str:
        """Render a template string with the given context.

        Args:
            template: Jinja2 template string.
            **context: Template variables.

        Returns:
            Rendered string.
        """
        return self.renderer.render_string(template, context)

    def get_model_by_name(self, name: str) -> ModelSpec | None:
        """Get a model spec by name.

        Args:
            name: The model name to find.

        Returns:
            The ModelSpec or None if not found.
        """
        for model in self.spec.models:
            if model.name == name:
                return model
        return None


class ModelGenerator(GeneratorBase):
    """Base class for generators that process individual models.

    Provides utilities for iterating over models and generating
    per-model files.
    """

    def generate_files(self) -> list[GeneratedFile]:
        """Generate files for all models.

        Returns:
            List of generated files.
        """
        files: list[GeneratedFile] = []

        # Generate shared/base files
        files.extend(self.generate_shared_files())

        # Generate per-model files
        for model in self.spec.models:
            files.extend(self.generate_model_files(model))

        # Generate index/aggregation files
        files.extend(self.generate_index_files())

        return files

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared files used by all models.

        Override in subclasses to generate base classes, utilities, etc.

        Returns:
            List of shared files.
        """
        return []

    @abstractmethod
    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate files for a single model.

        Args:
            model: The model specification.

        Returns:
            List of files for this model.
        """
        ...

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate index/aggregation files.

        Override in subclasses to generate __init__.py, schema.py, etc.

        Returns:
            List of index files.
        """
        return []


class CompositeGenerator(GeneratorBase):
    """A generator that combines multiple sub-generators.

    Useful for organizing related generators into a single unit.
    """

    def __init__(self, context: GeneratorContext) -> None:
        """Initialize the composite generator.

        Args:
            context: The generator context.
        """
        super().__init__(context)
        self.generators: list[GeneratorBase] = []

    def add_generator(self, generator: GeneratorBase) -> None:
        """Add a sub-generator.

        Args:
            generator: The generator to add.
        """
        self.generators.append(generator)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate files from all sub-generators.

        Returns:
            Combined list of files from all generators.
        """
        files: list[GeneratedFile] = []
        for generator in self.generators:
            files.extend(generator.generate_files())
        return files

    def generate(self) -> GeneratorResult:
        """Run all sub-generators.

        Returns:
            Combined result from all generators.
        """
        combined = GeneratorResult()

        for generator in self.generators:
            result = generator.generate()
            combined.files.extend(result.files)
            combined.written += result.written
            combined.skipped += result.skipped
            combined.errors.extend(result.errors)

        return combined


def create_init_file(
    module_path: Path,
    imports: list[str],
    all_exports: list[str],
    description: str = "",
    use_future_annotations: bool = False,
) -> GeneratedFile:
    """Create a Python __init__.py file.

    Args:
        module_path: Path for the __init__.py file.
        imports: List of import statements.
        all_exports: List of names for __all__.
        description: Module docstring.
        use_future_annotations: Add 'from __future__ import annotations' for forward references.

    Returns:
        GeneratedFile for the __init__.py.
    """
    lines = []

    if description:
        lines.append(f'"""{description}"""')
        lines.append("")

    if use_future_annotations:
        lines.append("from __future__ import annotations")
        lines.append("")

    if imports:
        lines.extend(imports)
        lines.append("")

    if all_exports:
        lines.append("__all__ = [")
        for name in sorted(all_exports):
            lines.append(f'    "{name}",')
        lines.append("]")
    else:
        lines.append("__all__: list[str] = []")

    content = "\n".join(lines) + "\n"

    return GeneratedFile(
        path=module_path / "__init__.py",
        content=content,
        strategy=FileStrategy.ALWAYS_OVERWRITE,
        description=f"Init file for {module_path}",
    )


__all__ = [
    "CompositeGenerator",
    "GeneratedFile",
    "GeneratorBase",
    "GeneratorContext",
    "GeneratorResult",
    "ModelGenerator",
    "create_init_file",
]
