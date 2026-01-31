from typing import Any

from kiarina.llm.app_context import get_app_context

from .._schemas.run_context import RunContext
from .._settings import settings_manager


def create_run_context(
    *,
    app_author: str | None = None,
    app_name: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    agent_id: str | None = None,
    runner_id: str | None = None,
    time_zone: str | None = None,
    language: str | None = None,
    currency: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunContext:
    settings = settings_manager.get_settings()

    if app_author is None or app_name is None:
        app_context = get_app_context()

        if app_author is None:
            app_author = app_context.app_author
        if app_name is None:
            app_name = app_context.app_name

    return RunContext(
        app_author=app_author,
        app_name=app_name,
        tenant_id=tenant_id if tenant_id is not None else settings.tenant_id,
        user_id=user_id if user_id is not None else settings.user_id,
        agent_id=agent_id if agent_id is not None else settings.agent_id,
        runner_id=runner_id if runner_id is not None else settings.runner_id,
        time_zone=time_zone if time_zone is not None else settings.time_zone,
        language=language if language is not None else settings.language,
        currency=currency if currency is not None else settings.currency,
        metadata=metadata if metadata is not None else settings.metadata,
    )
