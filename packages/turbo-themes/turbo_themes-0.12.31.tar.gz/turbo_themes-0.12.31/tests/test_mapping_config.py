# SPDX-License-Identifier: MIT
"""Tests for token mapping configuration."""

import pytest

from turbo_themes.mapping_config import (
    CoreMapping,
    OptionalGroupConfig,
    MappingConfig,
    load_mapping_config,
    get_mapping_config,
    resolve_token_path,
    build_token_getter,
    get_core_mappings_as_tuples,
)
from turbo_themes.themes import get_theme


class TestCoreMapping:
    """Tests for CoreMapping dataclass."""

    def test_create_without_fallback(self):
        """Can create mapping without fallback."""
        mapping = CoreMapping(css_var="bg-base", token_path="background.base")
        assert mapping.css_var == "bg-base"
        assert mapping.token_path == "background.base"
        assert mapping.fallback is None

    def test_create_with_fallback(self):
        """Can create mapping with fallback."""
        mapping = CoreMapping(
            css_var="table-cell-bg",
            token_path="content.table.cellBg",
            fallback="background.base",
        )
        assert mapping.fallback == "background.base"

    def test_is_frozen(self):
        """CoreMapping should be immutable."""
        mapping = CoreMapping(css_var="test", token_path="test.path")
        with pytest.raises(Exception):  # FrozenInstanceError
            mapping.css_var = "changed"  # type: ignore[misc]


class TestOptionalGroupConfig:
    """Tests for OptionalGroupConfig dataclass."""

    def test_create_with_properties(self):
        """Can create config with properties."""
        config = OptionalGroupConfig(
            prefix="spacing",
            properties=("xs", "sm", "md", "lg", "xl"),
        )
        assert config.prefix == "spacing"
        assert len(config.properties) == 5

    def test_create_with_mappings(self):
        """Can create config with mappings."""
        mapping = CoreMapping(
            css_var="duration-fast", token_path="animation.durationFast"
        )
        config = OptionalGroupConfig(
            prefix="animation",
            mappings=(mapping,),
        )
        assert len(config.mappings) == 1


class TestLoadMappingConfig:
    """Tests for load_mapping_config function."""

    def test_loads_config(self):
        """Should load configuration from JSON file."""
        config = load_mapping_config()
        assert isinstance(config, MappingConfig)
        assert config.prefix == "turbo"

    def test_has_core_mappings(self):
        """Config should have core mappings."""
        config = load_mapping_config()
        assert len(config.core_mappings) > 0

    def test_has_optional_groups(self):
        """Config should have optional groups."""
        config = load_mapping_config()
        assert "spacing" in config.optional_groups
        assert "elevation" in config.optional_groups


class TestGetMappingConfig:
    """Tests for get_mapping_config function."""

    def test_returns_cached_config(self):
        """Should return the same cached config on repeated calls."""
        config1 = get_mapping_config()
        config2 = get_mapping_config()
        assert config1 is config2

    def test_returns_mapping_config(self):
        """Should return a MappingConfig instance."""
        config = get_mapping_config()
        assert isinstance(config, MappingConfig)


class TestResolveTokenPath:
    """Tests for resolve_token_path function."""

    def test_resolves_simple_path(self):
        """Should resolve a simple nested path."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = resolve_token_path(theme.tokens, "background.base")
        assert value is not None
        assert isinstance(value, str)

    def test_resolves_deep_path(self):
        """Should resolve a deeply nested path."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = resolve_token_path(theme.tokens, "content.heading.h1")
        assert value is not None

    def test_returns_none_for_missing_path(self):
        """Should return None for non-existent paths."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = resolve_token_path(theme.tokens, "nonexistent.path")
        assert value is None

    def test_returns_none_for_partial_path(self):
        """Should return None when path is incomplete."""
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = resolve_token_path(theme.tokens, "background.nonexistent")
        assert value is None


class TestBuildTokenGetter:
    """Tests for build_token_getter function."""

    def test_returns_callable(self):
        """Should return a callable."""
        getter = build_token_getter("background.base")
        assert callable(getter)

    def test_getter_resolves_value(self):
        """Getter should resolve token values."""
        getter = build_token_getter("background.base")
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = getter(theme.tokens)
        assert value is not None

    def test_getter_returns_none_for_missing(self):
        """Getter should return None for missing paths."""
        getter = build_token_getter("nonexistent.path")
        theme = get_theme("catppuccin-mocha")
        assert theme is not None
        value = getter(theme.tokens)
        assert value is None


class TestGetCoreMappingsAsTuples:
    """Tests for get_core_mappings_as_tuples function."""

    def test_returns_list_of_tuples(self):
        """Should return a list of tuples."""
        mappings = get_core_mappings_as_tuples()
        assert isinstance(mappings, list)
        assert len(mappings) > 0
        assert isinstance(mappings[0], tuple)

    def test_tuples_have_correct_structure(self):
        """Each tuple should have (css_var, getter) structure."""
        mappings = get_core_mappings_as_tuples()
        for css_var, getter in mappings:
            assert isinstance(css_var, str)
            assert callable(getter)

    def test_getters_work_with_tokens(self):
        """Getters from tuples should work with actual tokens."""
        mappings = get_core_mappings_as_tuples()
        theme = get_theme("catppuccin-mocha")
        assert theme is not None

        # At least some getters should return values
        values = [getter(theme.tokens) for _, getter in mappings]
        non_none_values = [v for v in values if v is not None]
        assert len(non_none_values) > 0
