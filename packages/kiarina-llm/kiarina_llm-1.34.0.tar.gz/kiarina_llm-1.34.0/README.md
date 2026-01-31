# kiarina-llm

A Python library for LLM utilities and context management with type safety and configuration management.

## Features

- **AppContext Management**: Application-level context for platform directories
- **RunContext Management**: Structured context information for LLM pipeline processing
- **Type Safety**: Full type hints and Pydantic validation
- **Configuration Management**: Use `pydantic-settings-manager` for flexible configuration
- **Filesystem Safe Names**: Validated names for cross-platform compatibility
- **ID Validation**: Structured ID types with pattern validation

## Installation

```bash
pip install kiarina-llm
```

## Quick Start

### Basic Usage

```python
from kiarina.llm.run_context import create_run_context

# Create a run context
context = create_run_context(
    tenant_id="tenant-123",
    user_id="user-456",
    agent_id="my-agent",
    time_zone="Asia/Tokyo",
    language="ja"
)

print(f"User: {context.user_id}")
print(f"Agent: {context.agent_id}")
```

### Configuration

Configure defaults using `pydantic-settings-manager`:

```python
from kiarina.llm.run_context import settings_manager

settings_manager.user_config = {
    "tenant_id": "default-tenant",
    "time_zone": "America/New_York",
    "language": "en"
}
```

Or use environment variables:

```bash
export KIARINA_LLM_RUN_CONTEXT_TENANT_ID="prod-tenant"
export KIARINA_LLM_RUN_CONTEXT_TIME_ZONE="Asia/Tokyo"
```

## API Reference

### AppContext

Application-level context for platform directories:

```python
from kiarina.llm.app_context import get_app_context, settings_manager

# Configure app context
settings_manager.user_config = {
    "app_author": "MyCompany",
    "app_name": "MyAIApp"
}

# Get app context
app_context = get_app_context()
print(f"Author: {app_context.app_author}")
print(f"Name: {app_context.app_name}")
```

### RunContext

Run-level context for LLM pipeline processing:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `app_author` | `FSName` | Application author | `"MyCompany"` |
| `app_name` | `FSName` | Application name | `"MyAIApp"` |
| `tenant_id` | `IDStr` | Tenant identifier | `"tenant-123"` |
| `user_id` | `IDStr` | User identifier | `"user-456"` |
| `agent_id` | `IDStr` | Agent identifier | `"my-agent"` |
| `runner_id` | `IDStr` | Runner identifier | `"linux"` |
| `time_zone` | `str` | IANA time zone | `"Asia/Tokyo"` |
| `language` | `str` | Language code | `"ja"` |
| `currency` | `str` | Currency code | `"USD"` |
| `metadata` | `dict[str, Any]` | Additional metadata | `{"version": "1.0"}` |

## Type Validation

- **FSName**: Filesystem-safe names (alphanumeric, dots, underscores, hyphens, spaces)
- **IDStr**: Identifier strings (alphanumeric, dots, underscores, hyphens)

## Configuration Reference

### AppContext Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `app_author` | `KIARINA_LLM_APP_CONTEXT_APP_AUTHOR` | `"kiarina"` | Application author |
| `app_name` | `KIARINA_LLM_APP_CONTEXT_APP_NAME` | `"kiarina-llm"` | Application name |

### RunContext Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `tenant_id` | `KIARINA_LLM_RUN_CONTEXT_TENANT_ID` | `""` | Default tenant ID |
| `user_id` | `KIARINA_LLM_RUN_CONTEXT_USER_ID` | `""` | Default user ID |
| `agent_id` | `KIARINA_LLM_RUN_CONTEXT_AGENT_ID` | `""` | Default agent ID |
| `runner_id` | `KIARINA_LLM_RUN_CONTEXT_RUNNER_ID` | `platform.system().lower()` | Default runner ID |
| `time_zone` | `KIARINA_LLM_RUN_CONTEXT_TIME_ZONE` | `"UTC"` | Default time zone |
| `language` | `KIARINA_LLM_RUN_CONTEXT_LANGUAGE` | `"en"` | Default language |
| `currency` | `KIARINA_LLM_RUN_CONTEXT_CURRENCY` | `"USD"` | Default currency code |

## Development

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repository
git clone https://github.com/kiarina/kiarina-python.git
cd kiarina-python

# Setup development environment (installs tools, syncs dependencies, downloads test data)
mise run setup
```

### Running Tests

```bash
# Run format, lint, type checks and tests
mise run package kiarina-llm

# Coverage report
mise run package:test kiarina-llm --coverage

# Run specific tests
uv run --group test pytest packages/kiarina-llm/tests/run_context/
```

## Dependencies

- [pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## Roadmap

This package is in active development. Planned features include:

- **Chat Model Management**: Unified interface for different LLM providers
- **Agent Framework**: Tools for building LLM agents
- **Pipeline Management**: Workflow management for LLM processing
- **Memory Management**: Context and conversation memory handling
- **Tool Integration**: Framework for LLM tool calling

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project, but contributions are welcome! Please feel free to submit issues or pull requests.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package
