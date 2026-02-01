import pytest

from kiarina.lib.slack import settings_manager


def test_no_settings():
    with pytest.raises(ValueError):
        settings_manager.get_settings()
