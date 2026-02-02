"""Services generator for Prism.

Generates service classes with CRUD operations following the
base+extension pattern for customization.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.model import ModelSpec


class ServicesGenerator(ModelGenerator):
    """Generator for service classes."""

    REQUIRED_TEMPLATES = [
        "backend/services/base.py.jinja2",
        "backend/services/service_base.py.jinja2",
        "backend/services/service_extension.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.generator_config.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        package_base = backend_base / package_name
        self.services_path = package_base / self.generator_config.services_path
        self.generated_path = package_base / self.generator_config.services_generated_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared base service class."""
        return [
            self._generate_base_service(),
            self._generate_generated_init(),
        ]

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate service files for a single model."""
        files = [
            self._generate_base_service_for_model(model),
            self._generate_extension_service(model),
        ]
        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate __init__.py for services."""
        imports = []
        exports = []

        for model in self.spec.models:
            snake_name = to_snake_case(model.name)
            imports.append(f"from .{snake_name} import {model.name}Service")
            exports.append(f"{model.name}Service")

        return [
            create_init_file(
                self.services_path,
                imports,
                exports,
                "Service classes for business logic.",
            ),
        ]

    def _generate_base_service(self) -> GeneratedFile:
        """Generate the abstract base service class."""
        content = self.renderer.render_file(
            "backend/services/base.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.generated_path / "base.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Base service class",
        )

    def _generate_generated_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated folder."""
        imports = ["from .base import ServiceBase"]
        exports = ["ServiceBase"]

        for model in self.spec.models:
            snake_name = to_snake_case(model.name)
            imports.append(f"from .{snake_name}_base import {model.name}ServiceBase")
            exports.append(f"{model.name}ServiceBase")

        return create_init_file(
            self.generated_path,
            imports,
            exports,
            "Generated service base classes.",
        )

    def _generate_base_service_for_model(self, model: ModelSpec) -> GeneratedFile:
        """Generate the base service class for a model."""
        snake_name = to_snake_case(model.name)
        package_name = self.get_package_name()

        # Generate optional method code
        create_with_nested_method = None
        if model.nested_create:
            create_with_nested_method = self._generate_create_with_nested(model)

        temporal_methods = None
        if model.temporal:
            temporal_methods = self._generate_temporal_queries(model)

        # Build relationship metadata for filter handling
        relationships = [
            {
                "name": rel.name,
                "target_model": rel.target_model,
                "target_snake": to_snake_case(rel.target_model),
                "type": rel.type,
            }
            for rel in model.relationships
            if rel.type in ("one_to_many", "many_to_many")
        ]

        # Build M2M relationships for relationship management methods
        m2m_relationships = [
            {
                "name": rel.name,
                "target_model": rel.target_model,
                "target_snake": to_snake_case(rel.target_model),
            }
            for rel in model.relationships
            if rel.type == "many_to_many"
        ]

        content = self.renderer.render_file(
            "backend/services/service_base.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "package_name": package_name,
                "create_with_nested_method": create_with_nested_method,
                "temporal_methods": temporal_methods,
                "relationships": relationships,
                "m2m_relationships": m2m_relationships,
            },
        )
        return GeneratedFile(
            path=self.generated_path / f"{snake_name}_base.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Base service for {model.name}",
        )

    def _generate_create_with_nested(self, model: ModelSpec) -> str:
        """Generate create_with_nested method for a model."""
        if not model.nested_create:
            return ""

        snake_name = to_snake_case(model.name)
        package_name = self.get_package_name()

        # Build the nested creation logic
        nested_logic = []
        for rel_name in model.nested_create:
            rel_spec = next(
                (r for r in model.relationships if r.name == rel_name),
                None,
            )
            if rel_spec:
                target = rel_spec.target_model
                target_snake = to_snake_case(target)

                if rel_spec.type == "one_to_many":
                    nested_logic.append(f"""
        # Create nested {rel_name}
        if data.{rel_name}:
            from {package_name}.models.{target_snake} import {target}
            for child_data in data.{rel_name}:
                child = {target}(**child_data.model_dump(), {snake_name}_id=db_obj.id)
                self.db.add(child)""")
                elif rel_spec.type in ("one_to_one", "many_to_one"):
                    nested_logic.append(f"""
        # Create nested {rel_name}
        if data.{rel_name}:
            from {package_name}.models.{target_snake} import {target}
            child = {target}(**data.{rel_name}.model_dump())
            self.db.add(child)
            await self.db.flush()
            db_obj.{rel_name}_id = child.id""")

        nested_code = "\n".join(nested_logic)

        # Build the exclude set as a string
        exclude_set = "{" + ", ".join(f'"{rel}"' for rel in model.nested_create) + "}"

        return f'''

    async def create_with_nested(
        self,
        *,
        data: {model.name}CreateNested,
    ) -> {model.name}:
        """Create {model.name} with nested related entities in a single transaction.

        Args:
            data: The creation data including nested entities.

        Returns:
            The created {model.name} with nested entities.
        """
        from {package_name}.schemas.{snake_name} import {model.name}CreateNested

        # Create parent entity (exclude nested fields)
        parent_data = data.model_dump(exclude={exclude_set})
        db_obj = self.model(**parent_data)
        self.db.add(db_obj)
        await self.db.flush()  # Get the ID
{nested_code}

        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
'''

    def _generate_temporal_queries(self, model: ModelSpec) -> str:
        """Generate temporal query methods for time-series data."""
        if not model.temporal:
            return ""

        temporal = model.temporal
        timestamp_field = temporal.timestamp_field
        group_by_field = temporal.group_by_field

        methods = []

        if temporal.generate_latest_query:
            if group_by_field:
                methods.append(f'''

    async def get_latest(
        self,
        *,
        {group_by_field}: Any | None = None,
        include_deleted: bool = False,
    ) -> Sequence[{model.name}]:
        """Get the most recent record(s) based on {timestamp_field}.

        If {group_by_field} is provided, returns the latest record for that specific group.
        Otherwise, returns the latest record for each unique {group_by_field}.

        Args:
            {group_by_field}: Filter to a specific group.
            include_deleted: Whether to include soft-deleted records.

        Returns:
            List of latest {model.name} records.
        """
        from sqlalchemy import func

        # Subquery to find max timestamp per group
        subq = (
            select(
                self.model.{group_by_field},
                func.max(self.model.{timestamp_field}).label("max_ts")
            )
            .group_by(self.model.{group_by_field})
        )

        if hasattr(self.model, "deleted_at") and not include_deleted:
            subq = subq.where(self.model.deleted_at.is_(None))

        if {group_by_field} is not None:
            subq = subq.where(self.model.{group_by_field} == {group_by_field})

        subq = subq.subquery()

        # Join to get full records
        query = (
            select(self.model)
            .join(
                subq,
                and_(
                    self.model.{group_by_field} == subq.c.{group_by_field},
                    self.model.{timestamp_field} == subq.c.max_ts,
                ),
            )
        )

        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalars().all()
''')
            else:
                methods.append(f'''

    async def get_latest(
        self,
        *,
        include_deleted: bool = False,
    ) -> {model.name} | None:
        """Get the most recent record based on {timestamp_field}.

        Args:
            include_deleted: Whether to include soft-deleted records.

        Returns:
            The latest {model.name} record or None.
        """
        query = (
            select(self.model)
            .order_by(self.model.{timestamp_field}.desc())
            .limit(1)
        )

        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
''')

        if temporal.generate_history_query:
            methods.append(f'''

    async def get_history(
        self,
        *,
        start_date: Any | None = None,
        end_date: Any | None = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> Sequence[{model.name}]:
        """Get historical records within a date range.

        Args:
            start_date: Filter records on or after this date.
            end_date: Filter records on or before this date.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            include_deleted: Whether to include soft-deleted records.

        Returns:
            List of {model.name} records ordered by {timestamp_field}.
        """
        query = select(self.model).order_by(self.model.{timestamp_field}.desc())

        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        if start_date is not None:
            query = query.where(self.model.{timestamp_field} >= start_date)

        if end_date is not None:
            query = query.where(self.model.{timestamp_field} <= end_date)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()
''')

        return "\n".join(methods)

    def _generate_extension_service(self, model: ModelSpec) -> GeneratedFile:
        """Generate the user-extensible service class."""
        snake_name = to_snake_case(model.name)

        content = self.renderer.render_file(
            "backend/services/service_extension.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
            },
        )
        return GeneratedFile(
            path=self.services_path / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Extension service for {model.name}",
        )


__all__ = ["ServicesGenerator"]
