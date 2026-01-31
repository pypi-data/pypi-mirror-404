"""Shared pytest fixtures for turbo-themes tests."""

import pytest

from turbo_themes.manager import ThemeManager
from turbo_themes.themes import THEMES


@pytest.fixture
def manager():
    """Create a ThemeManager for testing.

    Returns:
        ThemeManager: A ThemeManager instance initialized with catppuccin-mocha theme.
    """
    return ThemeManager("catppuccin-mocha")


@pytest.fixture(params=list(THEMES.keys()))
def theme_id(request):
    """Parametrized fixture for all theme IDs.

    Args:
        request: Pytest request object providing access to the current parameter.

    Returns:
        str: A theme ID from the THEMES registry.
    """
    return request.param
