# SPDX-License-Identifier: MIT
"""Tests for type definitions."""

import pytest

from turbo_themes.models import (
    Appearance,
    TokenNamespace,
    Tokens,
    ThemeValue,
    ByVendorValue,
    Meta,
    TurboThemes,
    turbo_themes_from_dict,
)


class TestAppearance:
    """Tests for Appearance enum."""

    def test_light_value(self):
        """Light appearance should have correct value."""
        assert Appearance.LIGHT.value == "light"

    def test_dark_value(self):
        """Dark appearance should have correct value."""
        assert Appearance.DARK.value == "dark"

    def test_from_string(self):
        """Can create from string value."""
        assert Appearance("light") == Appearance.LIGHT
        assert Appearance("dark") == Appearance.DARK


class TestTokenNamespace:
    """Tests for TokenNamespace class."""

    def test_creates_from_dict(self):
        """Can create from dictionary."""
        ns = TokenNamespace({"key": "value"})
        assert ns.key == "value"

    def test_nested_dicts_become_namespaces(self):
        """Nested dicts should become TokenNamespace."""
        ns = TokenNamespace({"outer": {"inner": "value"}})
        assert isinstance(ns.outer, TokenNamespace)
        assert ns.outer.inner == "value"

    def test_missing_attr_returns_none(self):
        """Missing attributes should return None."""
        ns = TokenNamespace({"key": "value"})
        assert ns.nonexistent is None

    def test_repr(self):
        """Should have a useful repr."""
        ns = TokenNamespace({"key": "value"})
        assert "TokenNamespace" in repr(ns)

    def test_to_dict(self):
        """Should convert back to dictionary."""
        data = {"key": "value", "nested": {"inner": "data"}}
        ns = TokenNamespace(data)
        assert ns.to_dict() == data


class TestTokens:
    """Tests for Tokens dataclass."""

    def test_from_dict(self):
        """Can create from dictionary."""
        data = {
            "background": {"base": "#000"},
            "text": {"primary": "#fff"},
        }
        tokens = Tokens.from_dict(data)
        assert tokens.background.base == "#000"
        assert tokens.text.primary == "#fff"

    def test_to_dict(self):
        """Should convert back to dictionary."""
        data = {
            "background": {"base": "#000"},
            "text": {"primary": "#fff"},
        }
        tokens = Tokens.from_dict(data)
        assert tokens.to_dict() == data


class TestThemeValue:
    """Tests for ThemeValue dataclass."""

    @pytest.fixture
    def theme_data(self):
        """Sample theme data.

        Returns:
            Dict containing test theme data.
        """
        return {
            "id": "test-theme",
            "label": "Test Theme",
            "vendor": "test",
            "appearance": "dark",
            "tokens": {
                "background": {"base": "#000"},
                "text": {"primary": "#fff"},
            },
            "$description": "A test theme",
            "iconUrl": "https://example.com/icon.png",
        }

    def test_from_dict(self, theme_data):
        """Can create from dictionary.

        Args:
            theme_data: Sample theme data fixture.
        """
        theme = ThemeValue.from_dict(theme_data)
        assert theme.id == "test-theme"
        assert theme.label == "Test Theme"
        assert theme.vendor == "test"
        assert theme.appearance == Appearance.DARK

    def test_from_dict_with_optional_fields(self, theme_data):
        """Should parse optional fields.

        Args:
            theme_data: Sample theme data fixture.
        """
        theme = ThemeValue.from_dict(theme_data)
        assert theme.description == "A test theme"
        assert theme.icon_url == "https://example.com/icon.png"

    def test_from_dict_without_optional_fields(self):
        """Should handle missing optional fields."""
        data = {
            "id": "test",
            "label": "Test",
            "vendor": "test",
            "appearance": "light",
            "tokens": {"background": {"base": "#fff"}},
        }
        theme = ThemeValue.from_dict(data)
        assert theme.description is None
        assert theme.icon_url is None

    def test_to_dict(self, theme_data):
        """Should convert back to dictionary.

        Args:
            theme_data: Sample theme data fixture.
        """
        theme = ThemeValue.from_dict(theme_data)
        result = theme.to_dict()
        assert result["id"] == "test-theme"
        assert result["appearance"] == "dark"


class TestByVendorValue:
    """Tests for ByVendorValue dataclass."""

    def test_from_dict(self):
        """Can create from dictionary."""
        data = {
            "name": "Test Vendor",
            "homepage": "https://example.com",
            "themes": ["theme-1", "theme-2"],
        }
        vendor = ByVendorValue.from_dict(data)
        assert vendor.name == "Test Vendor"
        assert vendor.homepage == "https://example.com"
        assert vendor.themes == ["theme-1", "theme-2"]


class TestMeta:
    """Tests for Meta dataclass."""

    def test_from_dict(self):
        """Can create from dictionary."""
        data = {
            "themeIds": ["theme-1", "theme-2"],
            "vendors": ["vendor-1"],
            "totalThemes": 2,
            "lightThemes": 1,
            "darkThemes": 1,
        }
        meta = Meta.from_dict(data)
        assert meta.theme_ids == ["theme-1", "theme-2"]
        assert meta.total_themes == 2

    def test_from_dict_with_defaults(self):
        """Should use defaults for missing fields."""
        meta = Meta.from_dict({})
        assert meta.theme_ids == []
        assert meta.total_themes == 0


class TestTurboThemes:
    """Tests for TurboThemes dataclass."""

    @pytest.fixture
    def full_data(self):
        """Full TurboThemes data structure.

        Returns:
            Dict containing complete TurboThemes test data.
        """
        return {
            "$schema": "https://example.com/schema.json",
            "$version": "1.0.0",
            "$description": "Test themes",
            "$generated": "2024-01-01T00:00:00Z",
            "themes": {
                "test-theme": {
                    "id": "test-theme",
                    "label": "Test Theme",
                    "vendor": "test",
                    "appearance": "dark",
                    "tokens": {"background": {"base": "#000"}},
                }
            },
            "byVendor": {
                "test": {
                    "name": "Test Vendor",
                    "homepage": "https://example.com",
                    "themes": ["test-theme"],
                }
            },
            "meta": {
                "themeIds": ["test-theme"],
                "totalThemes": 1,
            },
        }

    def test_from_dict(self, full_data):
        """Can create from dictionary.

        Args:
            full_data: Full TurboThemes data fixture.
        """
        themes = TurboThemes.from_dict(full_data)
        assert "test-theme" in themes.themes
        assert themes.schema == "https://example.com/schema.json"

    def test_parses_themes(self, full_data):
        """Should parse theme values.

        Args:
            full_data: Full TurboThemes data fixture.
        """
        themes = TurboThemes.from_dict(full_data)
        theme = themes.themes["test-theme"]
        assert isinstance(theme, ThemeValue)
        assert theme.id == "test-theme"

    def test_parses_by_vendor(self, full_data):
        """Should parse vendor information.

        Args:
            full_data: Full TurboThemes data fixture.
        """
        themes = TurboThemes.from_dict(full_data)
        assert themes.by_vendor is not None
        assert "test" in themes.by_vendor

    def test_parses_meta(self, full_data):
        """Should parse metadata.

        Args:
            full_data: Full TurboThemes data fixture.
        """
        themes = TurboThemes.from_dict(full_data)
        assert themes.meta is not None
        assert themes.meta.total_themes == 1

    def test_parses_generated_timestamp(self, full_data):
        """Should parse generated timestamp.

        Args:
            full_data: Full TurboThemes data fixture.
        """
        themes = TurboThemes.from_dict(full_data)
        assert themes.generated is not None

    def test_handles_missing_optional_fields(self):
        """Should handle missing optional fields."""
        data = {
            "themes": {
                "test": {
                    "id": "test",
                    "label": "Test",
                    "vendor": "test",
                    "appearance": "dark",
                    "tokens": {},
                }
            }
        }
        themes = TurboThemes.from_dict(data)
        assert themes.by_vendor is None
        assert themes.meta is None


class TestTurboThemesFromDict:
    """Tests for turbo_themes_from_dict function."""

    def test_creates_turbo_themes(self):
        """Should create TurboThemes instance."""
        data = {
            "themes": {
                "test": {
                    "id": "test",
                    "label": "Test",
                    "vendor": "test",
                    "appearance": "light",
                    "tokens": {},
                }
            }
        }
        result = turbo_themes_from_dict(data)
        assert isinstance(result, TurboThemes)
