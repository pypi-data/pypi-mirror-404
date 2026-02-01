# Changelog

All notable changes to kiarina-lib-firebase-auth will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.35.0] - 2026-01-31

### Added
- `TokenDataCache` protocol for persistent token storage implementations
- `TokenManager` now supports `token_data_cache` parameter for automatic token persistence
- Automatic token data loading from cache on first `get_id_token()` call
- Automatic token data saving to cache after refresh

### Changed
- `TokenManager.refresh_token` and `TokenManager.token_data` are now properties that raise `AssertionError` if accessed before initialization

## [1.34.0] - 2026-01-31

### Changed
- **BREAKING**: Renamed `TokenResponse` to `TokenData` for better semantic clarity
- **BREAKING**: Changed `TokenData.expires_in` field to `TokenData.expires_at` (datetime) for improved usability
- **BREAKING**: Changed `TokenManager.__init__` to use keyword-only arguments with `api_key` required and either `refresh_token` or `token_data` required
- **BREAKING**: Changed `TokenManager.refresh()` return type from `TokenResponse` to `TokenData`

### Added
- `TokenData.from_api_response()` classmethod for creating TokenData from Firebase API responses
- Field order in `TokenData`: `refresh_token`, `id_token`, `expires_at` for better readability

### Fixed
- Fixed bug where `expires_at` property calculated incorrect expiration time on each access

## [1.33.1] - 2026-01-31

### Changed
- No changes

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
