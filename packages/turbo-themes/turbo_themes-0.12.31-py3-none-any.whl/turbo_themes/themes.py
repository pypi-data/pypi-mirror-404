# SPDX-License-Identifier: MIT
"""Theme registry for Turbo Themes.

Provides runtime access to all theme definitions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .models import TurboThemes, ThemeValue, turbo_themes_from_dict

# Load tokens at import time
_TOKENS_PATH = Path(__file__).parent / "tokens.json"
_tokens_data: TurboThemes | None = None


def _load_tokens() -> TurboThemes:
    """Load tokens from bundled JSON file.

    Returns:
        TurboThemes object containing all theme definitions.
    """
    global _tokens_data
    if _tokens_data is None:
        with open(_TOKENS_PATH, encoding="utf-8") as f:
            _tokens_data = turbo_themes_from_dict(json.load(f))
    return _tokens_data


def get_theme(theme_id: str) -> ThemeValue | None:
    """Get a theme by ID.

    Args:
        theme_id: The theme identifier (e.g., 'dracula', 'catppuccin-mocha')

    Returns:
        ThemeValue if found, None otherwise
    """
    tokens = _load_tokens()
    return tokens.themes.get(theme_id)


def get_all_themes() -> dict[str, ThemeValue]:
    """Get all available themes.

    Returns:
        Dict mapping theme IDs to ThemeValue objects
    """
    return _load_tokens().themes


def get_theme_ids() -> list[str]:
    """Get list of all theme IDs.

    Returns:
        List of theme ID strings
    """
    return list(_load_tokens().themes.keys())


# Pre-defined theme IDs for convenience
THEME_IDS: tuple[str, ...] = tuple(
    [
        "bulma-dark",
        "bulma-light",
        "catppuccin-frappe",
        "catppuccin-latte",
        "catppuccin-macchiato",
        "catppuccin-mocha",
        "dracula",
        "github-dark",
        "github-light",
    ]
)


# Lazy-loaded THEMES dict for backwards compatibility
class _ThemesProxy:
    """Lazy proxy for THEMES dict."""

    _cache: dict[str, ThemeValue] | None = None

    def __getitem__(self, key: str) -> ThemeValue:
        return get_all_themes()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(get_all_themes())

    def __len__(self) -> int:
        return len(THEME_IDS)

    def keys(self) -> Any:
        return get_all_themes().keys()

    def values(self) -> Any:
        return get_all_themes().values()

    def items(self) -> Any:
        return get_all_themes().items()

    def get(self, key: str, default: ThemeValue | None = None) -> ThemeValue | None:
        return get_all_themes().get(key, default)


THEMES = _ThemesProxy()


__all__ = [
    "get_theme",
    "get_all_themes",
    "get_theme_ids",
    "THEME_IDS",
    "THEMES",
    "ThemeValue",
    "TurboThemes",
]
