"""String case conversion utilities for Prism.

Provides functions to convert between different naming conventions:
- snake_case (Python, database)
- PascalCase (class names)
- camelCase (JavaScript/TypeScript)
- kebab-case (URLs, file names)
"""

from __future__ import annotations

import re


def to_snake_case(text: str) -> str:
    """Convert a string to snake_case.

    Examples:
        >>> to_snake_case("CustomerOrder")
        'customer_order'
        >>> to_snake_case("customer-order")
        'customer_order'
        >>> to_snake_case("customerOrder")
        'customer_order'
        >>> to_snake_case("HTTPResponse")
        'http_response'
    """
    # Handle empty string
    if not text:
        return ""

    # Replace hyphens and spaces with underscores
    text = re.sub(r"[-\s]+", "_", text)

    # Insert underscore before uppercase letters (handling acronyms)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    text = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", text)

    return text.lower()


def to_pascal_case(text: str) -> str:
    """Convert a string to PascalCase.

    Examples:
        >>> to_pascal_case("customer_order")
        'CustomerOrder'
        >>> to_pascal_case("customer-order")
        'CustomerOrder'
        >>> to_pascal_case("customerOrder")
        'CustomerOrder'
    """
    if not text:
        return ""

    # Split on underscores, hyphens, and spaces
    words = re.split(r"[-_\s]+", text)

    # Also split on camelCase boundaries
    result_words: list[str] = []
    for word in words:
        # Split camelCase
        parts = re.sub(r"([a-z])([A-Z])", r"\1_\2", word).split("_")
        result_words.extend(parts)

    return "".join(word.capitalize() for word in result_words if word)


def to_camel_case(text: str) -> str:
    """Convert a string to camelCase.

    Examples:
        >>> to_camel_case("customer_order")
        'customerOrder'
        >>> to_camel_case("CustomerOrder")
        'customerOrder'
        >>> to_camel_case("customer-order")
        'customerOrder'
    """
    pascal = to_pascal_case(text)
    if not pascal:
        return ""
    return pascal[0].lower() + pascal[1:]


def to_kebab_case(text: str) -> str:
    """Convert a string to kebab-case.

    Examples:
        >>> to_kebab_case("CustomerOrder")
        'customer-order'
        >>> to_kebab_case("customer_order")
        'customer-order'
        >>> to_kebab_case("customerOrder")
        'customer-order'
    """
    return to_snake_case(text).replace("_", "-")


def pluralize(word: str) -> str:
    """Pluralize an English word.

    This is a simple implementation that handles common cases.
    For more complex pluralization, consider using a library like inflect.

    Examples:
        >>> pluralize("customer")
        'customers'
        >>> pluralize("category")
        'categories'
        >>> pluralize("status")
        'statuses'
        >>> pluralize("child")
        'children'
    """
    if not word:
        return ""

    # Common irregular plurals
    irregulars = {
        "child": "children",
        "person": "people",
        "man": "men",
        "woman": "women",
        "foot": "feet",
        "tooth": "teeth",
        "goose": "geese",
        "mouse": "mice",
        "ox": "oxen",
    }

    lower = word.lower()
    if lower in irregulars:
        # Preserve original case
        if word[0].isupper():
            return irregulars[lower].capitalize()
        return irregulars[lower]

    # Words ending in -y preceded by a consonant
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiouAEIOU":
        return word[:-1] + "ies"

    # Words ending in -s, -x, -z, -ch, -sh
    if word.endswith(("s", "x", "z")) or word.endswith(("ch", "sh")):
        return word + "es"

    # Words ending in -f or -fe
    if word.endswith("f"):
        return word[:-1] + "ves"
    if word.endswith("fe"):
        return word[:-2] + "ves"

    # Default: add -s
    return word + "s"


def singularize(word: str) -> str:
    """Singularize an English word.

    This is a simple implementation that handles common cases.

    Examples:
        >>> singularize("customers")
        'customer'
        >>> singularize("categories")
        'category'
        >>> singularize("statuses")
        'status'
    """
    if not word:
        return ""

    # Common irregular plurals (reverse mapping)
    irregulars = {
        "children": "child",
        "people": "person",
        "men": "man",
        "women": "woman",
        "feet": "foot",
        "teeth": "tooth",
        "geese": "goose",
        "mice": "mouse",
        "oxen": "ox",
    }

    lower = word.lower()
    if lower in irregulars:
        if word[0].isupper():
            return irregulars[lower].capitalize()
        return irregulars[lower]

    # Words ending in -ies
    if word.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"

    # Words ending in -ves
    if word.endswith("ves"):
        # Could be -f or -fe
        base = word[:-3]
        if base + "f" in ["leaf", "loaf", "half", "calf", "wolf", "shelf", "self"]:
            return base + "f"
        return base + "fe"

    # Words ending in -es (for -s, -x, -z, -ch, -sh endings)
    if word.endswith("es") and len(word) > 2:
        base = word[:-2]
        if base.endswith(("s", "x", "z", "ch", "sh")):
            return base

    # Words ending in -s
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]

    return word


__all__ = [
    "pluralize",
    "singularize",
    "to_camel_case",
    "to_kebab_case",
    "to_pascal_case",
    "to_snake_case",
]
