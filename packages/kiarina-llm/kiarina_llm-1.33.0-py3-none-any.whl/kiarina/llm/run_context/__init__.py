from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._helpers.create_run_context import create_run_context
    from ._schemas.run_context import RunContext
    from ._settings import RunContextSettings, settings_manager
    from ._types.id_str import IDStr

__all__ = [
    # ._helpers
    "create_run_context",
    # ._schemas
    "RunContext",
    # ._settings
    "RunContextSettings",
    "settings_manager",
    # ._types
    "IDStr",
]


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._helpers
        "create_run_context": "._helpers.create_run_context",
        # ._schemas
        "RunContext": "._schemas.run_context",
        # ._settings
        "RunContextSettings": "._settings",
        "settings_manager": "._settings",
        # ._types
        "IDStr": "._types.id_str",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
