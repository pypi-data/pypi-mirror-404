"""Token mapping configuration loader.

Loads the centralized token-to-CSS-variable mappings from config/token-mappings.json.
This ensures Python uses the same mappings as TypeScript and other platforms.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .models import Tokens


@dataclass(frozen=True)
class CoreMapping:
    """A core token-to-CSS-variable mapping."""

    css_var: str
    token_path: str
    fallback: Optional[str] = None


@dataclass(frozen=True)
class OptionalGroupConfig:
    """Configuration for an optional token group."""

    prefix: str
    properties: Tuple[str, ...] = ()
    mappings: Tuple[CoreMapping, ...] = ()


@dataclass(frozen=True)
class MappingConfig:
    """Complete token mapping configuration."""

    prefix: str
    core_mappings: Tuple[CoreMapping, ...]
    optional_groups: Dict[str, OptionalGroupConfig]


def _find_config_path() -> Path:
    """Find the token-mappings.json config file.

    Searches relative to this module's location, going up to find the config directory.

    Returns:
        Path to the token-mappings.json file.

    Raises:
        FileNotFoundError: If the config file cannot be found.
    """
    # Start from this file's directory and traverse up
    current = Path(__file__).parent

    # Try different relative paths
    search_paths = [
        current / ".." / ".." / ".." / ".." / "config" / "token-mappings.json",
        current / ".." / ".." / ".." / "config" / "token-mappings.json",
        Path.cwd() / "config" / "token-mappings.json",
    ]

    for path in search_paths:
        resolved = path.resolve()
        if resolved.exists():
            return resolved

    raise FileNotFoundError(
        "Could not find config/token-mappings.json. "
        f"Searched: {[str(p.resolve()) for p in search_paths]}"
    )


def _parse_core_mapping(entry: Dict[str, Any]) -> CoreMapping:
    """Parse a core mapping entry from JSON.

    Args:
        entry: Dictionary containing cssVar, tokenPath, and optional fallback.

    Returns:
        CoreMapping dataclass instance.
    """
    return CoreMapping(
        css_var=entry["cssVar"],
        token_path=entry["tokenPath"],
        fallback=entry.get("fallback"),
    )


def _parse_optional_group(name: str, data: Dict[str, Any]) -> OptionalGroupConfig:
    """Parse an optional group configuration from JSON.

    Args:
        name: The name of the optional group (e.g., 'spacing', 'elevation').
        data: Dictionary containing prefix, properties, and optional mappings.

    Returns:
        OptionalGroupConfig dataclass instance.
    """
    properties = tuple(data.get("properties", []))
    mappings = tuple(_parse_core_mapping(m) for m in data.get("mappings", []))
    return OptionalGroupConfig(
        prefix=data.get("prefix", name),
        properties=properties,
        mappings=mappings,
    )


def load_mapping_config() -> MappingConfig:
    """Load the token mapping configuration from JSON.

    May raise FileNotFoundError if config file cannot be found,
    or json.JSONDecodeError if the config file is invalid JSON.

    Returns:
        Parsed MappingConfig object.
    """
    config_path = _find_config_path()
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    core_mappings = tuple(
        _parse_core_mapping(entry) for entry in data.get("coreMappings", [])
    )

    optional_groups = {
        name: _parse_optional_group(name, group_data)
        for name, group_data in data.get("optionalGroups", {}).items()
    }

    return MappingConfig(
        prefix=data.get("prefix", "turbo"),
        core_mappings=core_mappings,
        optional_groups=optional_groups,
    )


# Cached config instance
_cached_config: Optional[MappingConfig] = None


def get_mapping_config() -> MappingConfig:
    """Get the cached token mapping configuration.

    Loads the config on first access and caches it for subsequent calls.

    Returns:
        The cached MappingConfig object.
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_mapping_config()
    return _cached_config


def resolve_token_path(tokens: Tokens, path: str) -> Optional[str]:
    """Resolve a dot-separated path to a token value.

    Args:
        tokens: The Tokens object to traverse.
        path: Dot-separated path (e.g., 'background.base').

    Returns:
        The resolved string value, or None if the path doesn't exist.
    """
    parts = path.split(".")
    current: Any = tokens

    for part in parts:
        if current is None:
            return None

        # Handle attribute access for dataclasses/objects
        if hasattr(current, part):
            current = getattr(current, part)
        # Handle dict-like access
        elif hasattr(current, "__getitem__"):
            try:
                current = current[part]
            except (KeyError, TypeError):
                return None
        # Handle TokenNamespace with to_dict
        elif hasattr(current, "to_dict"):
            d = current.to_dict()
            current = d.get(part)
        else:
            return None

    return str(current) if current is not None else None


def build_token_getter(path: str) -> Callable[[Tokens], Optional[str]]:
    """Build a token getter function for a given path.

    Args:
        path: Dot-separated token path.

    Returns:
        A callable that takes Tokens and returns the value at the path.
    """

    def getter(tokens: Tokens) -> Optional[str]:
        return resolve_token_path(tokens, path)

    return getter


def get_core_mappings_as_tuples() -> (
    List[Tuple[str, Callable[[Tokens], Optional[str]]]]  # fmt: skip
):
    """Get core mappings as (css_suffix, getter) tuples.

    This provides backward compatibility with the old inline mapping style.

    Returns:
        List of (css_var_suffix, getter_function) tuples.
    """
    config = get_mapping_config()
    return [
        (mapping.css_var, build_token_getter(mapping.token_path))
        for mapping in config.core_mappings
    ]
