# SPDX-License-Identifier: MIT
"""Tests for generated token types."""

import pytest

from turbo_themes.generated import TurboTokens


class TestTurboTokensImport:
    """Tests for TurboTokens import from generated module."""

    def test_can_import_from_generated(self):
        """Should be able to import TurboTokens from generated module."""
        from turbo_themes.generated import TurboTokens

        assert TurboTokens is not None

    def test_can_import_from_tokens_submodule(self):
        """Should be able to import from tokens submodule."""
        from turbo_themes.generated.tokens import TurboTokens

        assert TurboTokens is not None


class TestTurboTokens:
    """Tests for TurboTokens dataclass."""

    def test_is_dataclass(self):
        """TurboTokens should be a dataclass."""
        import dataclasses

        assert dataclasses.is_dataclass(TurboTokens)

    def test_is_frozen(self):
        """TurboTokens should be frozen (immutable)."""
        tokens = TurboTokens()
        with pytest.raises(Exception):  # FrozenInstanceError
            tokens.bg_base = "changed"  # type: ignore[misc]

    def test_has_spacing_tokens(self):
        """Should have spacing tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "spacing_xs")
        assert hasattr(tokens, "spacing_sm")
        assert hasattr(tokens, "spacing_md")
        assert hasattr(tokens, "spacing_lg")
        assert hasattr(tokens, "spacing_xl")

    def test_has_elevation_tokens(self):
        """Should have elevation tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "elevation_none")
        assert hasattr(tokens, "elevation_sm")
        assert hasattr(tokens, "elevation_md")
        assert hasattr(tokens, "elevation_lg")
        assert hasattr(tokens, "elevation_xl")

    def test_has_animation_tokens(self):
        """Should have animation tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "animation_duration_fast")
        assert hasattr(tokens, "animation_duration_normal")
        assert hasattr(tokens, "animation_duration_slow")
        assert hasattr(tokens, "animation_easing_default")
        assert hasattr(tokens, "animation_easing_emphasized")

    def test_has_opacity_tokens(self):
        """Should have opacity tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "opacity_disabled")
        assert hasattr(tokens, "opacity_hover")
        assert hasattr(tokens, "opacity_pressed")

    def test_has_color_tokens(self):
        """Should have color tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "bg_base")
        assert hasattr(tokens, "text_primary")
        assert hasattr(tokens, "brand_primary")

    def test_has_typography_tokens(self):
        """Should have typography tokens."""
        tokens = TurboTokens()
        assert hasattr(tokens, "font_sans")
        assert hasattr(tokens, "font_mono")

    def test_default_values_are_strings(self):
        """All default values should be strings."""
        tokens = TurboTokens()
        assert isinstance(tokens.bg_base, str)
        assert isinstance(tokens.spacing_md, str)
        assert isinstance(tokens.elevation_md, str)

    def test_spacing_values_are_rem(self):
        """Spacing values should be in rem units."""
        tokens = TurboTokens()
        assert "rem" in tokens.spacing_xs
        assert "rem" in tokens.spacing_md
        assert "rem" in tokens.spacing_xl

    def test_animation_duration_values_are_ms(self):
        """Animation duration values should be in ms units."""
        tokens = TurboTokens()
        assert "ms" in tokens.animation_duration_fast
        assert "ms" in tokens.animation_duration_normal
        assert "ms" in tokens.animation_duration_slow

    def test_can_create_with_custom_values(self):
        """Should be able to create with custom values."""
        tokens = TurboTokens(bg_base="#ffffff", text_primary="#000000")
        assert tokens.bg_base == "#ffffff"
        assert tokens.text_primary == "#000000"

    def test_instance_equality(self):
        """Two instances with same values should be equal."""
        tokens1 = TurboTokens()
        tokens2 = TurboTokens()
        assert tokens1 == tokens2
