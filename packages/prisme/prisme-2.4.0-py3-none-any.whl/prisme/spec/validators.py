"""Validation helpers for Prism specifications.

This module contains validation logic that requires cross-model context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prisme.spec.project import ProjectSpec
    from prisme.spec.stack import StackSpec


def validate_auth_config(stack: StackSpec, project: ProjectSpec | None = None) -> list[str]:
    """Validate authentication configuration consistency.

    For JWT preset, checks that:
    1. User model exists if auth is enabled
    2. User model has required fields (username_field, password_hash, is_active, roles)
    3. password_hash field is excluded from API responses
    4. Default role exists in roles list (if roles are defined)

    For API key preset:
    - No user model validation is required
    - Only validates that auth is properly configured

    Args:
        stack: The complete stack specification
        project: The project specification (auth config lives here in v2)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # In v2, auth config lives on ProjectSpec
    if project is None:
        from prisme.spec.auth import AuthConfig

        auth = AuthConfig()
    else:
        auth = project.auth

    if not auth.enabled:
        return errors

    # API key auth doesn't require a user model or any of the JWT-specific validations
    if auth.preset == "api_key":
        return errors

    # Find user model (JWT preset only)
    user_model = None
    for model in stack.models:
        if model.name == auth.user_model:
            user_model = model
            break

    if not user_model:
        errors.append(
            f"Authentication is enabled but user model '{auth.user_model}' "
            f"not found in models list. Add a model with name='{auth.user_model}' "
            "or set auth.enabled=False."
        )
        return errors  # Can't continue validation without user model

    # Validate required fields exist
    required_fields = {
        auth.username_field,  # email or username
        "password_hash",
        "is_active",
        "roles",
    }

    model_field_names = {field.name for field in user_model.fields}
    missing = required_fields - model_field_names

    if missing:
        errors.append(
            f"User model '{user_model.name}' is missing required fields for "
            f"authentication: {sorted(missing)}. Add these fields to the model "
            "or disable authentication."
        )

    # Validate password_hash is hidden from API
    password_hash_field = None
    for field in user_model.fields:
        if field.name == "password_hash":
            password_hash_field = field
            break

    if password_hash_field and not password_hash_field.hidden:
        errors.append(
            f"Field 'password_hash' in user model '{user_model.name}' must have "
            "hidden=True to prevent exposure in API responses. This is a critical "
            "security requirement."
        )

    # Validate default role exists in roles list (if roles are defined)
    if auth.roles:
        role_names = {role.name for role in auth.roles}
        if auth.default_role not in role_names:
            errors.append(
                f"Default role '{auth.default_role}' is not defined in "
                f"auth.roles. Either add a role with name='{auth.default_role}' "
                "or change auth.default_role to an existing role."
            )

    return errors


def validate_model_relationships(stack: StackSpec) -> list[str]:
    """Validate that all relationship references point to existing models.

    Args:
        stack: The complete stack specification

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    model_names = {model.name for model in stack.models}

    for model in stack.models:
        for rel in model.relationships:
            if rel.target_model not in model_names:
                errors.append(
                    f"Model '{model.name}' has relationship '{rel.name}' targeting "
                    f"non-existent model '{rel.target_model}'. Available models: "
                    f"{sorted(model_names)}"
                )

    return errors


def validate_stack(stack: StackSpec, project: ProjectSpec | None = None) -> list[str]:
    """Run all validation checks on a stack specification.

    This is the main entry point for validation. It runs all validation
    functions and aggregates errors.

    Args:
        stack: The complete stack specification
        project: The project specification (optional)

    Returns:
        List of all validation error messages (empty if valid)
    """
    errors = []

    # Run all validators
    errors.extend(validate_auth_config(stack, project))
    errors.extend(validate_model_relationships(stack))

    return errors
