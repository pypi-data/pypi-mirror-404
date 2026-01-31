"""CSS variable generation utilities.

Provides focused helper functions for generating CSS custom properties
from theme tokens. Used by ThemeManager.apply_theme_to_css_variables().
"""

from __future__ import annotations

from typing import Dict, Optional

from .models import Tokens
from .mapping_config import (
    get_mapping_config,
    resolve_token_path,
    MappingConfig,
    OptionalGroupConfig,
)


def apply_core_mappings(
    tokens: Tokens,
    config: Optional[MappingConfig] = None,
) -> Dict[str, str]:
    """Apply core token mappings to generate CSS variables.

    Args:
        tokens: The theme tokens to map.
        config: Optional mapping configuration. Uses default if not provided.

    Returns:
        Dictionary of CSS variable names to values.
    """
    if config is None:
        config = get_mapping_config()

    variables: Dict[str, str] = {}
    prefix = config.prefix

    for mapping in config.core_mappings:
        try:
            value = resolve_token_path(tokens, mapping.token_path)
            # Try fallback if primary path didn't resolve
            if value is None and mapping.fallback:
                value = resolve_token_path(tokens, mapping.fallback)
            if value is not None:
                variables[f"--{prefix}-{mapping.css_var}"] = str(value)
        except (AttributeError, KeyError):
            pass

    return variables


def apply_optional_spacing(
    tokens: Tokens,
    config: Optional[OptionalGroupConfig] = None,
    prefix: str = "turbo",
) -> Dict[str, str]:
    """Apply optional spacing tokens to generate CSS variables.

    Args:
        tokens: The theme tokens containing spacing.
        config: Optional spacing group configuration.
        prefix: CSS variable prefix.

    Returns:
        Dictionary of spacing CSS variable names to values.
    """
    variables: Dict[str, str] = {}

    if not tokens.spacing:
        return variables

    if config is None:
        mapping_config = get_mapping_config()
        config = mapping_config.optional_groups.get("spacing")
        prefix = mapping_config.prefix

    if config is None:
        return variables

    spacing = tokens.spacing
    for prop in config.properties:
        value = getattr(spacing, prop, None)
        if value is not None:
            variables[f"--{prefix}-{config.prefix}-{prop}"] = str(value)

    return variables


def apply_optional_elevation(
    tokens: Tokens,
    config: Optional[OptionalGroupConfig] = None,
    prefix: str = "turbo",
) -> Dict[str, str]:
    """Apply optional elevation tokens to generate CSS variables.

    Args:
        tokens: The theme tokens containing elevation.
        config: Optional elevation group configuration.
        prefix: CSS variable prefix.

    Returns:
        Dictionary of elevation CSS variable names to values.
    """
    variables: Dict[str, str] = {}

    if not tokens.elevation:
        return variables

    if config is None:
        mapping_config = get_mapping_config()
        config = mapping_config.optional_groups.get("elevation")
        prefix = mapping_config.prefix

    if config is None:
        return variables

    elevation = tokens.elevation
    for prop in config.properties:
        value = getattr(elevation, prop, None)
        if value is not None:
            variables[f"--{prefix}-{config.prefix}-{prop}"] = str(value)

    return variables


def apply_optional_animation(
    tokens: Tokens,
    config: Optional[OptionalGroupConfig] = None,
    prefix: str = "turbo",
) -> Dict[str, str]:
    """Apply optional animation tokens to generate CSS variables.

    Args:
        tokens: The theme tokens containing animation.
        config: Optional animation group configuration.
        prefix: CSS variable prefix.

    Returns:
        Dictionary of animation CSS variable names to values.
    """
    variables: Dict[str, str] = {}

    if not tokens.animation:
        return variables

    if config is None:
        mapping_config = get_mapping_config()
        config = mapping_config.optional_groups.get("animation")
        prefix = mapping_config.prefix

    if config is None or not config.mappings:
        return variables

    for mapping in config.mappings:
        value = resolve_token_path(tokens, mapping.token_path)
        if value is not None:
            variables[f"--{prefix}-{config.prefix}-{mapping.css_var}"] = str(value)

    return variables


def apply_optional_opacity(
    tokens: Tokens,
    config: Optional[OptionalGroupConfig] = None,
    prefix: str = "turbo",
) -> Dict[str, str]:
    """Apply optional opacity tokens to generate CSS variables.

    Args:
        tokens: The theme tokens containing opacity.
        config: Optional opacity group configuration.
        prefix: CSS variable prefix.

    Returns:
        Dictionary of opacity CSS variable names to values.
    """
    variables: Dict[str, str] = {}

    if not tokens.opacity:
        return variables

    if config is None:
        mapping_config = get_mapping_config()
        config = mapping_config.optional_groups.get("opacity")
        prefix = mapping_config.prefix

    if config is None:
        return variables

    opacity = tokens.opacity
    for prop in config.properties:
        value = getattr(opacity, prop, None)
        if value is not None:
            variables[f"--{prefix}-{config.prefix}-{prop}"] = str(value)

    return variables


def generate_css_variables(tokens: Tokens) -> Dict[str, str]:
    """Generate all CSS variables from theme tokens.

    This is a convenience function that combines all mapping categories:
    core mappings, spacing, elevation, animation, and opacity.

    Args:
        tokens: The theme tokens to convert.

    Returns:
        Complete dictionary of CSS variable names to values.
    """
    config = get_mapping_config()
    prefix = config.prefix

    variables: Dict[str, str] = {}

    # Apply all mapping categories
    variables.update(apply_core_mappings(tokens, config))
    variables.update(
        apply_optional_spacing(
            tokens,
            config.optional_groups.get("spacing"),
            prefix,
        )
    )
    variables.update(
        apply_optional_elevation(
            tokens,
            config.optional_groups.get("elevation"),
            prefix,
        )
    )
    variables.update(
        apply_optional_animation(
            tokens,
            config.optional_groups.get("animation"),
            prefix,
        )
    )
    variables.update(
        apply_optional_opacity(
            tokens,
            config.optional_groups.get("opacity"),
            prefix,
        )
    )

    return variables
