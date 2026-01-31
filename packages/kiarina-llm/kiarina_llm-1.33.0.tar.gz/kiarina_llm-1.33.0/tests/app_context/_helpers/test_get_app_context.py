from kiarina.llm.app_context import get_app_context, settings_manager


def test_get_app_context() -> None:
    app_context = get_app_context()
    assert app_context.app_author == settings_manager.settings.app_author
    assert app_context.app_name == settings_manager.settings.app_name
