# SPDX-License-Identifier: MIT
"""Tests for CSS variable generation utilities."""

from turbo_themes.css_variables import (
    apply_core_mappings,
    apply_optional_spacing,
    apply_optional_elevation,
    apply_optional_animation,
    apply_optional_opacity,
    generate_css_variables,
)
from turbo_themes.themes import get_theme
from turbo_themes.mapping_config import get_mapping_config


class TestApplyCoreMappings:
    """Tests for apply_core_mappings function."""

    def test_returns_dict(self):
        """Core mappings should return a dictionary."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_core_mappings(theme.tokens)
        assert isinstance(result, dict)

    def test_contains_expected_variables(self):
        """Should contain expected CSS variables."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_core_mappings(theme.tokens)
        assert "--turbo-bg-base" in result
        assert "--turbo-text-primary" in result
        assert "--turbo-brand-primary" in result

    def test_uses_prefix_from_config(self):
        """Variables should use the configured prefix."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_core_mappings(theme.tokens)
        # All keys should start with --turbo-
        for key in result:
            assert key.startswith("--turbo-")

    def test_with_custom_config(self):
        """Should use custom config when provided."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        config = get_mapping_config()
        result = apply_core_mappings(theme.tokens, config)
        assert len(result) > 0


class TestApplyOptionalSpacing:
    """Tests for apply_optional_spacing function."""

    def test_returns_empty_when_no_spacing(self):
        """Should return empty dict when theme has no spacing tokens."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_optional_spacing(theme.tokens)
        # catppuccin-mocha doesn't have spacing tokens
        assert result == {}

    def test_returns_spacing_vars_when_available(self):
        """Should return spacing variables for themes that have them.

        Note: Currently no themes have spacing tokens, so this test
        verifies the function handles empty spacing gracefully.
        When a theme with spacing is added, update this test.
        """
        theme = get_theme("dracula")
        assert theme is not None
        result = apply_optional_spacing(theme.tokens)
        # Verify function returns dict (empty or populated)
        assert isinstance(result, dict)
        # Explicit assertion: if theme has spacing, result should have spacing vars
        if theme.tokens.spacing:
            assert (
                len(result) > 0
            ), "Theme has spacing tokens but no variables generated"
            assert any("spacing" in key for key in result)
        else:
            # Explicit assertion for when theme has no spacing
            assert result == {}, "No spacing tokens means empty result"


class TestApplyOptionalElevation:
    """Tests for apply_optional_elevation function."""

    def test_returns_empty_when_no_elevation(self):
        """Should return empty dict when theme has no elevation tokens."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_optional_elevation(theme.tokens)
        assert result == {}

    def test_returns_elevation_vars_when_available(self):
        """Should return elevation variables for themes that have them.

        Note: Currently no themes have elevation tokens, so this test
        verifies the function handles empty elevation gracefully.
        """
        theme = get_theme("dracula")
        assert theme is not None
        result = apply_optional_elevation(theme.tokens)
        assert isinstance(result, dict)
        if theme.tokens.elevation:
            assert (
                len(result) > 0
            ), "Theme has elevation tokens but no variables generated"
        else:
            assert result == {}, "No elevation tokens means empty result"


class TestApplyOptionalAnimation:
    """Tests for apply_optional_animation function."""

    def test_returns_empty_when_no_animation(self):
        """Should return empty dict when theme has no animation tokens."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_optional_animation(theme.tokens)
        assert result == {}

    def test_returns_animation_vars_when_available(self):
        """Should return animation variables for themes that have them.

        Note: Currently no themes have animation tokens, so this test
        verifies the function handles empty animation gracefully.
        """
        theme = get_theme("dracula")
        assert theme is not None
        result = apply_optional_animation(theme.tokens)
        assert isinstance(result, dict)
        if theme.tokens.animation:
            assert (
                len(result) > 0
            ), "Theme has animation tokens but no variables generated"
        else:
            assert result == {}, "No animation tokens means empty result"


class TestApplyOptionalOpacity:
    """Tests for apply_optional_opacity function."""

    def test_returns_empty_when_no_opacity(self):
        """Should return empty dict when theme has no opacity tokens."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = apply_optional_opacity(theme.tokens)
        assert result == {}

    def test_returns_opacity_vars_when_available(self):
        """Should return opacity variables for themes that have them.

        Note: Currently no themes have opacity tokens, so this test
        verifies the function handles empty opacity gracefully.
        """
        theme = get_theme("dracula")
        assert theme is not None
        result = apply_optional_opacity(theme.tokens)
        assert isinstance(result, dict)
        if theme.tokens.opacity:
            assert (
                len(result) > 0
            ), "Theme has opacity tokens but no variables generated"
        else:
            assert result == {}, "No opacity tokens means empty result"


class TestGenerateCssVariables:
    """Tests for generate_css_variables function."""

    def test_returns_dict(self):
        """Should return a dictionary of CSS variables."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = generate_css_variables(theme.tokens)
        assert isinstance(result, dict)

    def test_includes_core_mappings(self):
        """Should include core CSS variables."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        result = generate_css_variables(theme.tokens)
        assert "--turbo-bg-base" in result
        assert "--turbo-text-primary" in result

    def test_includes_optional_when_available(self):
        """Should include optional variables when theme has them.

        This test verifies that optional token groups are included in
        the generated CSS variables when present in the theme.
        """
        theme = get_theme("dracula")
        assert theme is not None
        result = generate_css_variables(theme.tokens)
        # Should at least have core variables
        assert len(result) > 0
        # Explicit assertions for optional token inclusion
        if theme.tokens.spacing:
            assert any(
                "spacing" in key for key in result
            ), "Spacing tokens present but not in CSS variables"
        if theme.tokens.elevation:
            assert any(
                "elevation" in key for key in result
            ), "Elevation tokens present but not in CSS variables"
        if theme.tokens.animation:
            assert any(
                "animation" in key for key in result
            ), "Animation tokens present but not in CSS variables"
        if theme.tokens.opacity:
            assert any(
                "opacity" in key for key in result
            ), "Opacity tokens present but not in CSS variables"

    def test_all_themes_generate_without_error(self):
        """All themes should generate CSS variables without errors."""
        from turbo_themes.themes import get_all_themes

        for theme_id, theme in get_all_themes().items():
            result = generate_css_variables(theme.tokens)
            assert isinstance(result, dict), f"Failed for theme: {theme_id}"
            assert len(result) > 0, f"No variables generated for: {theme_id}"
