import pytest

from kiarina.i18n import catalog, settings_manager


@pytest.fixture(autouse=True)
def clear_i18n_caches():
    """Clear i18n caches and settings before and after each test."""
    catalog.clear()

    yield

    catalog.clear()
    settings_manager.user_config = {}
    settings_manager.cli_args = {}
