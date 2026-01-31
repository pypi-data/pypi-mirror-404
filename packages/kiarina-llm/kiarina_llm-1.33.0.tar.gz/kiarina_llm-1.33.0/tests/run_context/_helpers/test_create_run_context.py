from kiarina.llm.app_context import get_app_context
from kiarina.llm.run_context import create_run_context, settings_manager


def test_no_args():
    settings = settings_manager.get_settings()

    app_context = get_app_context()
    run_context = create_run_context()

    assert run_context.app_author == app_context.app_author
    assert run_context.app_name == app_context.app_name
    assert run_context.tenant_id == settings.tenant_id
    assert run_context.user_id == settings.user_id
    assert run_context.time_zone == settings.time_zone
    assert run_context.language == settings.language
    assert run_context.currency == settings.currency
    assert run_context.metadata == settings.metadata


def test_with_args():
    context = create_run_context(
        app_author="TestCompany",
        app_name="TestApp",
        tenant_id="tenant-123",
        user_id="user-456",
        agent_id="agent-789",
        runner_id="test-runner",
        time_zone="Asia/Tokyo",
        language="ja",
        currency="JPY",
        metadata={"version": "1.0.0"},
    )

    assert context.app_author == "TestCompany"
    assert context.app_name == "TestApp"
    assert context.tenant_id == "tenant-123"
    assert context.user_id == "user-456"
    assert context.agent_id == "agent-789"
    assert context.runner_id == "test-runner"
    assert context.time_zone == "Asia/Tokyo"
    assert context.language == "ja"
    assert context.currency == "JPY"
    assert context.metadata == {"version": "1.0.0"}
