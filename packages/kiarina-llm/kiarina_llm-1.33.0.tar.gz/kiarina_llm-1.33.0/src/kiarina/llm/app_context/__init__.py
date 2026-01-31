from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._helpers.get_app_context import get_app_context
    from ._models.app_context import AppContext
    from ._settings import AppContextSettings, settings_manager
    from ._types.fs_name import FSName

__all__ = [
    # ._helpers
    "get_app_context",
    # ._models
    "AppContext",
    # ._settings
    "AppContextSettings",
    "settings_manager",
    # ._types
    "FSName",
]


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module {__name__} has no attribute {name}")

    module_map = {
        # ._helpers
        "get_app_context": "._helpers.get_app_context",
        # ._models
        "AppContext": "._models.app_context",
        # ._settings
        "AppContextSettings": "._settings",
        "settings_manager": "._settings",
        # ._types
        "FSName": "._types.fs_name",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
