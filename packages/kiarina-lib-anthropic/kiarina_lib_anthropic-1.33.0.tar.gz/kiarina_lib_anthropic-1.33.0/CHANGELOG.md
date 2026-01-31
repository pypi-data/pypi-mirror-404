# Changelog

All notable changes to kiarina-lib-anthropic will be documented in this file.

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

### Changed
- No changes

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

### Changed
- No changes

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
- No changes

## [1.15.0] - 2025-12-13

### Changed
- No changes

## [1.14.0] - 2025-12-13

### Changed
- No changes

## [1.13.0] - 2025-12-09

### Changed
- No changes

## [1.12.0] - 2025-12-05

### Changed
- No changes

## [1.11.2] - 2025-12-02

### Changed
- No changes

## [1.11.1] - 2025-12-01

### Changed
- Made `api_key` field optional (can be `None`) to support environment variable configuration without explicit settings

## [1.11.0] - 2025-12-01

### Added
- Initial release with Anthropic API configuration management
- `AnthropicSettings` class with API key and base URL support
- API key protection using `SecretStr`
- Multiple configuration support via `pydantic-settings-manager`
- Environment variable configuration with `KIARINA_LIB_ANTHROPIC_` prefix
- Custom base URL support for Anthropic-compatible APIs
