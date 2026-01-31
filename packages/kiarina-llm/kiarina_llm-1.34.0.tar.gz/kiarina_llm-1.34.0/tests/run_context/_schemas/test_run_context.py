import pytest

from kiarina.llm.run_context import RunContext


def test_valid():
    data = {
        "app_author": "TestCompany",
        "app_name": "TestApp",
        "tenant_id": "tenant-123",
        "user_id": "user-456",
        "agent_id": "agent-789",
        "runner_id": "runner-001",
        "time_zone": "UTC",
        "language": "en",
        "currency": "USD",
        "metadata": {"key": "value"},
    }

    run_context = RunContext.model_validate(data)
    assert run_context.model_dump() == data


def test_invalid():
    with pytest.raises(Exception):
        RunContext.model_validate(
            {
                "app_author": "Invalid/Name",  # Invalid character
                "app_name": "TestApp",
                "tenant_id": "tenant-123",
                "user_id": "user-456",
                "agent_id": "agent-789",
                "runner_id": "runner-001",
                "time_zone": "UTC",
                "language": "en",
                "currency": "USD",
            }
        )


def test_with_metadata_empty():
    """Test with_metadata() with empty initial metadata"""
    context = RunContext.model_validate(
        {
            "app_author": "TestCompany",
            "app_name": "TestApp",
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "agent_id": "agent-789",
            "runner_id": "runner-001",
            "time_zone": "UTC",
            "language": "en",
            "currency": "USD",
        }
    )

    new_context = context.with_metadata(version="1.0", env="prod")

    # Original context should be unchanged
    assert context.metadata == {}

    # New context should have updated metadata
    assert new_context.metadata == {"version": "1.0", "env": "prod"}

    # Other fields should be the same
    assert new_context.app_author == context.app_author
    assert new_context.tenant_id == context.tenant_id


def test_with_metadata_merge():
    """Test with_metadata() merges with existing metadata"""
    context = RunContext.model_validate(
        {
            "app_author": "TestCompany",
            "app_name": "TestApp",
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "agent_id": "agent-789",
            "runner_id": "runner-001",
            "time_zone": "UTC",
            "language": "en",
            "currency": "USD",
            "metadata": {"version": "1.0", "existing": "value"},
        }
    )

    new_context = context.with_metadata(version="2.0", env="prod")

    # Original context should be unchanged
    assert context.metadata == {"version": "1.0", "existing": "value"}

    # New context should have merged metadata (version updated, existing preserved, env added)
    assert new_context.metadata == {
        "version": "2.0",
        "existing": "value",
        "env": "prod",
    }


def test_with_metadata_chaining():
    """Test with_metadata() can be chained"""
    context = RunContext.model_validate(
        {
            "app_author": "TestCompany",
            "app_name": "TestApp",
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "agent_id": "agent-789",
            "runner_id": "runner-001",
            "time_zone": "UTC",
            "language": "en",
            "currency": "USD",
        }
    )

    new_context = (
        context.with_metadata(version="1.0")
        .with_metadata(env="prod")
        .with_metadata(debug=True)
    )

    assert new_context.metadata == {"version": "1.0", "env": "prod", "debug": True}
