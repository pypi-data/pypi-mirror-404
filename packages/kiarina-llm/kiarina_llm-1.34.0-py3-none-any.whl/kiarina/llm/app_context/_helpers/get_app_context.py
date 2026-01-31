from .._models.app_context import AppContext
from .._settings import settings_manager


def get_app_context() -> AppContext:
    settings = settings_manager.get_settings()

    return AppContext(
        app_author=settings.app_author,
        app_name=settings.app_name,
    )
