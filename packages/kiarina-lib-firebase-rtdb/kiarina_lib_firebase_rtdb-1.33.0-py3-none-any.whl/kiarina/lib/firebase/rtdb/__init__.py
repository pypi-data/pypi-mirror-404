import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._exceptions.rtdb_stream_cancelled_error import RTDBStreamCancelledError
    from ._helpers.get_data import get_data
    from ._helpers.watch_data import watch_data
    from ._schemas.data_change_event import DataChangeEvent
    from ._settings import RTDBSettings, settings_manager

__all__ = [
    # ._exceptions
    "RTDBStreamCancelledError",
    # ._helpers
    "get_data",
    "watch_data",
    # ._schemas
    "DataChangeEvent",
    # ._settings
    "RTDBSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module {__name__} has no attribute {name}")

    module_map = {
        # ._exceptions
        "RTDBStreamCancelledError": "._exceptions.rtdb_stream_cancelled_error",
        # ._helpers
        "get_data": "._helpers.get_data",
        "watch_data": "._helpers.watch_data",
        # ._schemas
        "DataChangeEvent": "._schemas.data_change_event",
        # ._settings
        "RTDBSettings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
