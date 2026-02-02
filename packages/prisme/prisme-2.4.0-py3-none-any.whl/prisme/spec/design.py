"""Design system configuration for Prism.

This module defines the design system configuration including theme,
colors, typography, and component styling options.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ThemePreset(str, Enum):
    """Available theme presets."""

    NORDIC = "nordic"
    """Clean, muted, sophisticated - slate/sky color palette."""

    MINIMAL = "minimal"
    """Ultra-clean with subtle grays - neutral color palette."""

    CORPORATE = "corporate"
    """Professional blue-based palette - blue/slate colors."""


class IconSet(str, Enum):
    """Available icon libraries."""

    LUCIDE = "lucide"
    """Lucide React - MIT licensed, tree-shakeable, 1400+ icons."""

    HEROICONS = "heroicons"
    """Heroicons - MIT licensed, by Tailwind Labs."""


class FontFamily(str, Enum):
    """Font family presets."""

    INTER = "inter"
    """Inter - Modern, highly legible sans-serif."""

    SYSTEM = "system"
    """System UI fonts - Native look on each platform."""

    GEIST = "geist"
    """Geist - Vercel's modern font family."""


class BorderRadius(str, Enum):
    """Border radius presets."""

    NONE = "none"
    """No border radius - sharp corners."""

    SM = "sm"
    """Small radius - 4px."""

    MD = "md"
    """Medium radius - 8px (default)."""

    LG = "lg"
    """Large radius - 12px."""

    FULL = "full"
    """Full radius - pill shapes."""


class DesignSystemConfig(BaseModel):
    """Design system configuration.

    Controls the visual appearance of generated frontend components
    including theme, colors, typography, and component styling.

    Example:
        >>> config = DesignSystemConfig(
        ...     theme="nordic",
        ...     dark_mode=True,
        ...     icon_set="lucide",
        ...     border_radius="md",
        ... )

        >>> # With custom primary color
        >>> config = DesignSystemConfig(
        ...     theme="minimal",
        ...     primary_color="#2563eb",
        ... )
    """

    # Theme selection
    theme: ThemePreset = Field(
        default=ThemePreset.NORDIC,
        description="Theme preset: 'nordic', 'minimal', or 'corporate'",
    )

    # Color overrides
    primary_color: str | None = Field(
        default=None,
        description="Override primary color (CSS color value or RGB triplet)",
    )
    accent_color: str | None = Field(
        default=None,
        description="Override accent color (CSS color value or RGB triplet)",
    )

    # Dark mode
    dark_mode: bool = Field(
        default=True,
        description="Enable dark mode toggle and styles",
    )
    default_theme: str = Field(
        default="system",
        description="Default theme: 'light', 'dark', or 'system'",
    )

    # Icons
    icon_set: IconSet = Field(
        default=IconSet.LUCIDE,
        description="Icon library to use: 'lucide' or 'heroicons'",
    )

    # Typography
    font_family: FontFamily = Field(
        default=FontFamily.INTER,
        description="Font family preset: 'inter', 'system', or 'geist'",
    )
    custom_font_url: str | None = Field(
        default=None,
        description="Custom font URL (Google Fonts, etc.) - overrides font_family",
    )

    # Component styling
    border_radius: BorderRadius = Field(
        default=BorderRadius.MD,
        description="Border radius preset: 'none', 'sm', 'md', 'lg', or 'full'",
    )
    enable_animations: bool = Field(
        default=True,
        description="Enable transition animations",
    )

    model_config = {"extra": "forbid"}

    def get_font_css_import(self) -> str | None:
        """Get the CSS import statement for the configured font.

        Returns:
            CSS @import statement or None if using system fonts.
        """
        if self.custom_font_url:
            return f'@import url("{self.custom_font_url}");'

        font_urls = {
            FontFamily.INTER: (
                '@import url("https://fonts.googleapis.com/css2?family=Inter:'
                'wght@400;500;600;700&display=swap");'
            ),
            FontFamily.GEIST: (
                '@import url("https://fonts.googleapis.com/css2?family=Geist:'
                'wght@400;500;600;700&display=swap");'
            ),
            FontFamily.SYSTEM: None,
        }
        return font_urls.get(self.font_family)

    def get_font_family_css(self) -> str:
        """Get the CSS font-family value.

        Returns:
            CSS font-family value string.
        """
        font_stacks = {
            FontFamily.INTER: (
                "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            ),
            FontFamily.GEIST: (
                "'Geist', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            ),
            FontFamily.SYSTEM: (
                "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
                "Roboto, 'Helvetica Neue', Arial, sans-serif"
            ),
        }
        return font_stacks.get(self.font_family, font_stacks[FontFamily.SYSTEM])

    def get_icon_package(self) -> str:
        """Get the npm package name for the configured icon set.

        Returns:
            npm package name.
        """
        packages = {
            IconSet.LUCIDE: "lucide-react",
            IconSet.HEROICONS: "@heroicons/react",
        }
        return packages[self.icon_set]

    def get_icon_package_version(self) -> str:
        """Get the npm package version for the configured icon set.

        Returns:
            npm package version string.
        """
        versions = {
            IconSet.LUCIDE: "^0.460.0",
            IconSet.HEROICONS: "^2.2.0",
        }
        return versions[self.icon_set]

    def get_radius_css(self) -> str:
        """Get the CSS border-radius value.

        Returns:
            CSS border-radius value.
        """
        radii = {
            BorderRadius.NONE: "0",
            BorderRadius.SM: "0.25rem",
            BorderRadius.MD: "0.5rem",
            BorderRadius.LG: "0.75rem",
            BorderRadius.FULL: "9999px",
        }
        return radii[self.border_radius]
