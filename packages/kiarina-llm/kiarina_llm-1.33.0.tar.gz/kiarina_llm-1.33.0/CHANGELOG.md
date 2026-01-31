# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.33.0] - 2026-01-31

### Changed
- No changes

## [1.32.0] - 2026-01-30

### Changed
- No changes

## [1.31.1] - 2026-01-29

### Changed
- No changes

## [1.31.0] - 2026-01-29

### Changed
- No changes

## [1.30.0] - 2026-01-27

### Changed
- No changes

## [1.29.0] - 2026-01-16

### Changed
- No changes

## [1.28.0] - 2026-01-16

### Changed
- No changes

## [1.27.0] - 2026-01-12

### Changed
- No changes

## [1.26.0] - 2026-01-09

### Changed
- No changes

## [1.25.1] - 2026-01-08

### Changed
- No changes

## [1.25.0] - 2026-01-08

### Changed
- No changes

## [1.24.0] - 2026-01-08

### Changed
- No changes

## [1.23.0] - 2026-01-06

### Added
- Added `with_metadata()` method to `RunContext` for creating new instances with updated metadata

## [1.22.1] - 2026-01-06

### Changed
- No changes

## [1.22.0] - 2026-01-05

### Changed
- No changes

## [1.21.1] - 2026-01-05

### Changed
- No changes

## [1.21.0] - 2025-12-30

### Added
- **AppContext**: New `kiarina.llm.app_context` subpackage for application-level context management
  - `AppContext` model with `app_author` and `app_name` fields
  - `AppContextSettings` for configuration management
  - `get_app_context()` helper function
  - `FSName` type moved from `run_context` to `app_context`

### Changed
- **RunContext**: Refactored to use `AppContext` for application-level settings
  - `create_run_context()` now uses `get_app_context()` for `app_author` and `app_name` defaults
  - Moved `app_author` and `app_name` settings from `RunContextSettings` to `AppContextSettings`
  - Renamed `_models/` directory to `_schemas/` for better clarity
  - Moved `settings.py` to `_settings.py` to indicate internal implementation

### Removed
- **Content measurement utilities**: Removed `kiarina.llm.content` subpackage
  - Removed `ContentLimits`, `ContentMetrics`, `ContentScale` models
  - Removed `calculate_overflow()` function
  - These features were experimental and not yet production-ready

## [1.20.1] - 2025-12-25

### Changed
- No changes

## [1.20.0] - 2025-12-19

### Changed
- No changes

## [1.19.0] - 2025-12-19

### Changed
- No changes

## [1.18.2] - 2025-12-17

### Changed
- No changes

## [1.18.1] - 2025-12-16

### Changed
- No changes

## [1.18.0] - 2025-12-16

### Changed
- No changes

## [1.17.0] - 2025-12-15

### Changed
- No changes

## [1.16.0] - 2025-12-15

### Changed
- No changes

## [1.15.1] - 2025-12-14

### Changed
- Refactored internal module structure to follow project architecture rules
  - Moved `_registry.py` to `_helpers/create_run_context.py`
  - Moved `_model.py` to `_models/run_context.py`
- Added default values to `RunContext` fields: `time_zone="UTC"`, `language="en"`, `currency="USD"`

## [1.15.0] - 2025-12-13

### Changed
- No changes

## [1.14.0] - 2025-12-13

### Changed
- No changes

## [1.13.0] - 2025-12-09

### Added
- Add `currency` field to `RunContext` model for currency information management

## [1.12.0] - 2025-12-05

### Changed
- No changes

## [1.11.2] - 2025-12-02

### Changed
- No changes

## [1.11.1] - 2025-12-01

### Changed
- No changes

## [1.11.0] - 2025-12-01

### Changed
- No changes

## [1.10.0] - 2025-12-01

### Changed
- No changes

## [1.9.0] - 2025-11-26

### Changed
- No changes

## [1.8.0] - 2025-10-24

### Changed
- No changes

## [1.7.0] - 2025-10-21

### Changed
- No changes

## [1.6.3] - 2025-10-13

### Changed
- Updated `pydantic-settings-manager` dependency from `>=2.1.0` to `>=2.3.0`

## [1.6.2] - 2025-10-10

### Changed
- No changes

## [1.6.1] - 2025-10-10

### Changed
- No changes

## [1.6.0] - 2025-10-10

### Changed
- No changes

## [1.5.0] - 2025-10-10

### Changed
- No changes

## [1.4.0] - 2025-10-09

### Changed
- No changes

## [1.3.0] - 2025-10-05

### Changed
- No changes

## [1.2.0] - 2025-09-25

### Added
- **Content measurement utilities**: Comprehensive utilities for measuring and managing LLM-handled content
  - `ContentMetrics`: Tracks token count, file sizes, file counts by type, and media durations
  - `ContentLimits`: Defines limits for different content types with feature flags
  - `ContentScale`: Enum for content scale categories (SMALL, MEDIUM, LARGE, EXTRA_LARGE)
  - `calculate_overflow`: Calculates overflow amounts when content exceeds defined limits
- **Type safety**: Full type hints and Pydantic validation for all content models
- **Feature flags**: Enable/disable specific input types (image, audio, video)
- **Lazy loading**: Efficient module loading using `__getattr__`

## [1.1.1] - 2025-09-11

### Changed
- No changes

## [1.1.0] - 2025-09-11

### Changed
- No changes

## [1.0.1] - 2025-09-11

### Changed
- No changes - version bump for consistency with other packages

## [1.0.0] - 2025-09-09

### Added
- Initial release of kiarina-llm
- RunContext management for LLM pipeline processing
- Type-safe FSName validation for filesystem-safe names
- Type-safe IDStr validation for identifiers
- Configuration management using pydantic-settings-manager
- Environment variable configuration support
- Runtime configuration overrides
- Cross-platform compatibility with Windows reserved name validation
- Full type hints and Pydantic validation
- Comprehensive test suite

### Features
- **RunContext**: Structured context information holder
  - Application author and name (filesystem safe)
  - Tenant, user, agent, and runner identifiers
  - Time zone and language settings
  - Extensible metadata support
- **Type Safety**: Custom Pydantic types for validation
  - FSName: Filesystem-safe names with cross-platform validation
  - IDStr: Identifier strings with pattern validation
- **Configuration**: Flexible settings management
  - Environment variable support with KIARINA_LLM_RUN_CONTEXT_ prefix
  - Runtime configuration overrides
  - Default value management

### Dependencies
- pydantic>=2.10.1
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
