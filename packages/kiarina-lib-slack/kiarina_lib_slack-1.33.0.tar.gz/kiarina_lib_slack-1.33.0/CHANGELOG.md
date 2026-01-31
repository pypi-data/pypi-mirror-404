# Changelog

All notable changes to kiarina-lib-slack will be documented in this file.

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

### Added
- Initial release with Slack API configuration management
- `SlackSettings` class with comprehensive Slack App configuration support
- Secure credential handling using `SecretStr` for sensitive fields (client_secret, signing_secret, app_token, bot_token)
- Multiple configuration support via `pydantic-settings-manager`
- Environment variable configuration with `KIARINA_LIB_SLACK_` prefix
- Support for OAuth scopes, team/enterprise IDs, and file installation store configuration
