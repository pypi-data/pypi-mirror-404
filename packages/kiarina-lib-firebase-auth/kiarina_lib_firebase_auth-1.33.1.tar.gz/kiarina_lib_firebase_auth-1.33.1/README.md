# kiarina-lib-firebase-auth

Firebase authentication library with REST API integration and automatic token management.

## Purpose

`kiarina-lib-firebase-auth` provides a simple and secure way to manage Firebase authentication using REST APIs. This library enables custom token exchange and automatic ID token lifecycle management with configuration management using pydantic-settings-manager.

Key features:
- Custom token exchange for refresh/ID tokens via Firebase REST API
- Automatic ID token lifecycle management with `TokenManager`
- Token refresh 5 minutes before expiration
- Thread-safe token refresh with `asyncio.Lock`
- Secure API key management with SecretStr
- Multi-configuration support for different projects/environments
- Async-only API for modern Python applications
- Environment variable configuration

## Installation

```bash
pip install kiarina-lib-firebase-auth
```

## Quick Start

### Basic Usage

```python
from kiarina.lib.firebase.auth import (
    TokenManager,
    exchange_custom_token,
    settings_manager,
)

# Configure settings
settings_manager.user_config = {
    "default": {
        "project_id": "your-project-id",
        "api_key": "your-firebase-api-key",
    }
}

# Get settings
settings = settings_manager.get_settings()
api_key = settings.api_key.get_secret_value()

# Exchange custom token for ID and refresh tokens
custom_token = "your_custom_token_here"
response = await exchange_custom_token(custom_token, api_key)

# Create token manager for automatic token refresh
manager = TokenManager(
    refresh_token=response.refresh_token,
    api_key=api_key,
)

# Get ID token (automatically refreshes when needed)
id_token = await manager.get_id_token()
print(f"ID Token: {id_token}")

# Use the ID token for Firebase API calls
# The token will be automatically refreshed 5 minutes before expiration
```

### Manual Token Refresh

```python
from kiarina.lib.firebase.auth import refresh_id_token

# Manually refresh ID token using refresh token
response = await refresh_id_token(
    refresh_token="your_refresh_token",
    api_key="your_api_key",
)

print(f"New ID Token: {response.id_token}")
print(f"Expires at: {response.expires_at}")
```

## API Reference

### Settings

#### `FirebaseAuthSettings`

Configuration for Firebase authentication.

```python
from pydantic import SecretStr
from kiarina.lib.firebase.auth import FirebaseAuthSettings

settings = FirebaseAuthSettings(
    project_id="your-project-id",
    api_key=SecretStr("your-firebase-api-key"),
)
```

**Fields:**
- `project_id: str` - Firebase project ID
- `api_key: SecretStr` - Firebase Web API Key (obtain from Firebase Console)

### Functions

#### `exchange_custom_token(custom_token: str, api_key: str) -> TokenResponse`

Exchange a Firebase custom token for an ID token and refresh token.

**Parameters:**
- `custom_token: str` - Firebase custom token (JWT)
- `api_key: str` - Firebase Web API Key

**Returns:**
- `TokenResponse` - Contains `id_token`, `refresh_token`, and `expires_in`

**Raises:**
- `InvalidCustomTokenError` - If the custom token is invalid or expired
- `FirebaseAPIError` - If Firebase API returns an error

#### `refresh_id_token(refresh_token: str, api_key: str) -> TokenResponse`

Refresh ID token using refresh token.

**Parameters:**
- `refresh_token: str` - Firebase refresh token
- `api_key: str` - Firebase Web API Key

**Returns:**
- `TokenResponse` - Contains new `id_token`, `refresh_token`, and `expires_in`

**Raises:**
- `InvalidRefreshTokenError` - If refresh token is invalid or expired
- `FirebaseAPIError` - If Firebase API returns an error

### Classes

#### `TokenManager`

Service class for automatic ID token lifecycle management.

```python
from kiarina.lib.firebase.auth import TokenManager

manager = TokenManager(
    refresh_token="your_refresh_token",
    api_key="your_api_key",
    id_token="optional_initial_id_token",  # Optional
    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),  # Optional
    refresh_buffer_seconds=300,  # Default: 5 minutes
)
```

**Constructor Parameters:**
- `refresh_token: str` - Firebase refresh token
- `api_key: str` - Firebase Web API Key
- `id_token: str | None` - Initial ID token (optional)
- `expires_at: datetime | None` - Initial expiration time (optional)
- `refresh_buffer_seconds: int` - Refresh buffer time in seconds (default: 300)

**Methods:**
- `async get_id_token() -> str` - Get current ID token (auto-refreshes if needed)
- `async refresh() -> TokenResponse` - Manually refresh ID token

**Properties:**
- `id_token: str` - Current ID token
- `expires_at: datetime` - Token expiration time (UTC)

#### `TokenResponse`

Schema for Firebase token exchange responses.

**Fields:**
- `id_token: str` - Firebase ID token (JWT)
- `refresh_token: str` - Refresh token for getting new ID tokens
- `expires_in: int` - ID token lifetime in seconds

**Properties:**
- `expires_at: datetime` - Calculated expiration datetime (UTC)

### Exceptions

#### `FirebaseAuthError`

Base exception for Firebase Auth errors.

#### `InvalidCustomTokenError`

Raised when custom token is invalid or expired.

#### `InvalidRefreshTokenError`

Raised when refresh token is invalid or expired.

#### `FirebaseAPIError`

Raised when Firebase API returns an error response.

**Attributes:**
- `status_code: int | None` - HTTP status code
- `error_code: str | None` - Firebase error code

## Configuration

### YAML Configuration

```yaml
kiarina.lib.firebase.auth:
  default:
    project_id: your-project-id
    api_key: your-firebase-api-key

  production:
    project_id: prod-project-id
    api_key: ${FIREBASE_API_KEY}  # From environment variable
```

### Environment Variables

Settings can be configured via environment variables with the `KIARINA_LIB_FIREBASE_AUTH_` prefix:

```bash
export KIARINA_LIB_FIREBASE_AUTH_PROJECT_ID=your-project-id
export KIARINA_LIB_FIREBASE_AUTH_API_KEY=your-firebase-api-key
```

### Multi-Configuration Support

```python
from kiarina.lib.firebase.auth import settings_manager

# Configure multiple environments
settings_manager.user_config = {
    "development": {
        "project_id": "dev-project",
        "api_key": "dev-api-key",
    },
    "production": {
        "project_id": "prod-project",
        "api_key": "prod-api-key",
    },
}

# Get settings for specific environment
dev_settings = settings_manager.get_settings("development")
prod_settings = settings_manager.get_settings("production")
```

## Testing

This package includes integration tests that require Firebase Admin SDK and Google Cloud authentication.

### Setup

1. Create a test settings file:

```yaml
# test_settings.yaml
kiarina.lib.google.auth:
  default:
    type: service_account
    project_id: your-project-id
    service_account_email: your-service-account@your-project.iam.gserviceaccount.com
    service_account_file: ~/.gcp/service-account/your-project/key.json

kiarina.lib.firebase.auth:
  default:
    project_id: your-project-id
    api_key: your-firebase-api-key
```

2. Set environment variable:

```bash
export KIARINA_LIB_FIREBASE_AUTH_TEST_SETTINGS_FILE=/path/to/test_settings.yaml
```

3. Run tests:

```bash
pytest tests/
```

## Dependencies

- `httpx>=0.28.1` - Async HTTP client for Firebase REST API
- `pydantic>=2.10.6` - Data validation and settings management
- `pydantic-settings>=2.10.1` - Settings management from environment
- `pydantic-settings-manager>=2.3.0` - Multi-configuration settings management

### Development Dependencies

- `firebase-admin>=6.6.0` - Firebase Admin SDK (for testing)
- `kiarina-lib-google-auth>=1.22.0` - Google Cloud authentication (for testing)

## License

This project is licensed under the MIT License.

## Related Projects

- [kiarina-lib-google-auth](https://github.com/kiarina/kiarina-python/tree/main/packages/kiarina-lib-google-auth) - Google Cloud authentication library
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Multi-configuration settings management
