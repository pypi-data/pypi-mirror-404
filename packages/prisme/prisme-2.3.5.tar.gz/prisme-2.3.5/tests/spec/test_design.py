"""Tests for design system specification models."""

import pytest

from prisme.spec.design import (
    BorderRadius,
    DesignSystemConfig,
    FontFamily,
    IconSet,
    ThemePreset,
)


class TestDesignSystemConfig:
    """Tests for DesignSystemConfig model."""

    def test_default_values(self):
        """Design config has sensible defaults."""
        config = DesignSystemConfig()
        assert config.theme == ThemePreset.NORDIC
        assert config.dark_mode is True
        assert config.icon_set == IconSet.LUCIDE
        assert config.font_family == FontFamily.INTER
        assert config.border_radius == BorderRadius.MD
        assert config.enable_animations is True

    def test_theme_preset_nordic(self):
        """Nordic theme is the default."""
        config = DesignSystemConfig(theme=ThemePreset.NORDIC)
        assert config.theme == ThemePreset.NORDIC
        assert config.theme.value == "nordic"

    def test_theme_preset_minimal(self):
        """Can use minimal theme."""
        config = DesignSystemConfig(theme=ThemePreset.MINIMAL)
        assert config.theme == ThemePreset.MINIMAL
        assert config.theme.value == "minimal"

    def test_theme_preset_corporate(self):
        """Can use corporate theme."""
        config = DesignSystemConfig(theme=ThemePreset.CORPORATE)
        assert config.theme == ThemePreset.CORPORATE
        assert config.theme.value == "corporate"

    def test_custom_primary_color(self):
        """Can set custom primary color."""
        config = DesignSystemConfig(primary_color="#2563eb")
        assert config.primary_color == "#2563eb"

    def test_custom_accent_color(self):
        """Can set custom accent color."""
        config = DesignSystemConfig(accent_color="14 165 233")
        assert config.accent_color == "14 165 233"

    def test_dark_mode_disabled(self):
        """Can disable dark mode."""
        config = DesignSystemConfig(dark_mode=False)
        assert config.dark_mode is False

    def test_default_theme_options(self):
        """Can set default theme to light, dark, or system."""
        for theme in ["light", "dark", "system"]:
            config = DesignSystemConfig(default_theme=theme)
            assert config.default_theme == theme


class TestIconSet:
    """Tests for IconSet enum."""

    def test_lucide_icon_set(self):
        """Lucide is the default icon set."""
        config = DesignSystemConfig()
        assert config.icon_set == IconSet.LUCIDE

    def test_heroicons_icon_set(self):
        """Can use Heroicons."""
        config = DesignSystemConfig(icon_set=IconSet.HEROICONS)
        assert config.icon_set == IconSet.HEROICONS

    def test_get_icon_package_lucide(self):
        """Returns correct npm package for Lucide."""
        config = DesignSystemConfig(icon_set=IconSet.LUCIDE)
        assert config.get_icon_package() == "lucide-react"

    def test_get_icon_package_heroicons(self):
        """Returns correct npm package for Heroicons."""
        config = DesignSystemConfig(icon_set=IconSet.HEROICONS)
        assert config.get_icon_package() == "@heroicons/react"

    def test_get_icon_package_version_lucide(self):
        """Returns version for Lucide package."""
        config = DesignSystemConfig(icon_set=IconSet.LUCIDE)
        version = config.get_icon_package_version()
        assert version.startswith("^")
        assert "0.460" in version

    def test_get_icon_package_version_heroicons(self):
        """Returns version for Heroicons package."""
        config = DesignSystemConfig(icon_set=IconSet.HEROICONS)
        version = config.get_icon_package_version()
        assert version.startswith("^")
        assert "2." in version


class TestFontFamily:
    """Tests for FontFamily enum."""

    def test_inter_font_family(self):
        """Inter is the default font family."""
        config = DesignSystemConfig()
        assert config.font_family == FontFamily.INTER

    def test_system_font_family(self):
        """Can use system fonts."""
        config = DesignSystemConfig(font_family=FontFamily.SYSTEM)
        assert config.font_family == FontFamily.SYSTEM

    def test_geist_font_family(self):
        """Can use Geist font."""
        config = DesignSystemConfig(font_family=FontFamily.GEIST)
        assert config.font_family == FontFamily.GEIST

    def test_get_font_css_import_inter(self):
        """Returns Google Fonts import for Inter."""
        config = DesignSystemConfig(font_family=FontFamily.INTER)
        import_statement = config.get_font_css_import()
        assert import_statement is not None
        assert "fonts.googleapis.com" in import_statement
        assert "Inter" in import_statement

    def test_get_font_css_import_system(self):
        """Returns None for system fonts."""
        config = DesignSystemConfig(font_family=FontFamily.SYSTEM)
        assert config.get_font_css_import() is None

    def test_get_font_css_import_custom(self):
        """Custom font URL overrides font_family."""
        custom_url = "https://fonts.example.com/custom-font.css"
        config = DesignSystemConfig(font_family=FontFamily.INTER, custom_font_url=custom_url)
        import_statement = config.get_font_css_import()
        assert custom_url in import_statement

    def test_get_font_family_css_inter(self):
        """Returns correct CSS font-family for Inter."""
        config = DesignSystemConfig(font_family=FontFamily.INTER)
        css = config.get_font_family_css()
        assert "'Inter'" in css
        assert "system-ui" in css

    def test_get_font_family_css_system(self):
        """Returns correct CSS font-family for system fonts."""
        config = DesignSystemConfig(font_family=FontFamily.SYSTEM)
        css = config.get_font_family_css()
        assert "system-ui" in css
        assert "Roboto" in css


class TestBorderRadius:
    """Tests for BorderRadius enum."""

    def test_border_radius_none(self):
        """Can use no border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.NONE)
        assert config.border_radius == BorderRadius.NONE

    def test_border_radius_sm(self):
        """Can use small border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.SM)
        assert config.border_radius == BorderRadius.SM

    def test_border_radius_md(self):
        """Medium border radius is default."""
        config = DesignSystemConfig()
        assert config.border_radius == BorderRadius.MD

    def test_border_radius_lg(self):
        """Can use large border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.LG)
        assert config.border_radius == BorderRadius.LG

    def test_border_radius_full(self):
        """Can use full (pill) border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.FULL)
        assert config.border_radius == BorderRadius.FULL

    def test_get_radius_css_none(self):
        """Returns 0 for no border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.NONE)
        assert config.get_radius_css() == "0"

    def test_get_radius_css_md(self):
        """Returns 0.5rem for medium border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.MD)
        assert config.get_radius_css() == "0.5rem"

    def test_get_radius_css_full(self):
        """Returns 9999px for full border radius."""
        config = DesignSystemConfig(border_radius=BorderRadius.FULL)
        assert config.get_radius_css() == "9999px"


class TestDesignSystemConfigValidation:
    """Tests for config validation."""

    def test_extra_fields_forbidden(self):
        """Extra fields are not allowed."""
        with pytest.raises(ValueError):
            DesignSystemConfig(invalid_field="value")

    def test_all_combinations_valid(self):
        """Can combine all configuration options."""
        config = DesignSystemConfig(
            theme=ThemePreset.MINIMAL,
            primary_color="#1e40af",
            accent_color="#0ea5e9",
            dark_mode=True,
            default_theme="dark",
            icon_set=IconSet.LUCIDE,
            font_family=FontFamily.GEIST,
            border_radius=BorderRadius.LG,
            enable_animations=False,
        )
        assert config.theme == ThemePreset.MINIMAL
        assert config.primary_color == "#1e40af"
        assert config.dark_mode is True
        assert config.icon_set == IconSet.LUCIDE
        assert config.font_family == FontFamily.GEIST
        assert config.border_radius == BorderRadius.LG
        assert config.enable_animations is False
