import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._settings import SlackSettings, settings_manager

__version__ = version("kiarina-lib-slack")

__all__ = [
    # ._settings
    "SlackSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._settings
        "SlackSettings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
