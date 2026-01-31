# Changelog

All notable changes to kiarina-lib-firebase-auth will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.33.0] - 2026-01-31

### Changed
- No changes

## [1.32.0] - 2026-01-30

### Added
- Initial release with Firebase authentication REST API integration
- `exchange_custom_token()` function for custom token exchange
- `refresh_id_token()` function for ID token refresh
- `TokenManager` service class for automatic ID token lifecycle management
- `TokenResponse` schema for Firebase token exchange responses
- `FirebaseAuthSettings` for configuration management
- Exception classes: `FirebaseAuthError`, `InvalidCustomTokenError`, `InvalidRefreshTokenError`, `FirebaseAPIError`
- Secure API key management with SecretStr
- Multi-configuration support via pydantic-settings-manager
- Thread-safe token refresh with asyncio.Lock
- Automatic token refresh 5 minutes before expiration
- Async-only API for modern Python applications
- Environment variable configuration with `KIARINA_LIB_FIREBASE_AUTH_` prefix
