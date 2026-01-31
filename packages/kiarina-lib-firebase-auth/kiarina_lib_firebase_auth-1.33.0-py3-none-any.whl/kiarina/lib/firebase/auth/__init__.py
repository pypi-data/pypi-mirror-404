import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._exceptions.firebase_api_error import FirebaseAPIError
    from ._exceptions.firebase_auth_error import FirebaseAuthError
    from ._exceptions.invalid_custom_token_error import InvalidCustomTokenError
    from ._exceptions.invalid_refresh_token_error import InvalidRefreshTokenError
    from ._schemas.token_response import TokenResponse
    from ._services.token_manager import TokenManager
    from ._settings import FirebaseAuthSettings, settings_manager
    from ._utils.exchange_custom_token import exchange_custom_token
    from ._utils.refresh_id_token import refresh_id_token

__all__ = [
    # ._exceptions
    "FirebaseAPIError",
    "FirebaseAuthError",
    "InvalidCustomTokenError",
    "InvalidRefreshTokenError",
    # ._schemas
    "TokenResponse",
    # ._services
    "TokenManager",
    # ._settings
    "FirebaseAuthSettings",
    "settings_manager",
    # ._utils
    "exchange_custom_token",
    "refresh_id_token",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module {__name__} has no attribute {name}")

    module_map = {
        # ._exceptions
        "FirebaseAPIError": "._exceptions.firebase_api_error",
        "FirebaseAuthError": "._exceptions.firebase_auth_error",
        "InvalidCustomTokenError": "._exceptions.invalid_custom_token_error",
        "InvalidRefreshTokenError": "._exceptions.invalid_refresh_token_error",
        # ._schemas
        "TokenResponse": "._schemas.token_response",
        # ._services
        "TokenManager": "._services.token_manager",
        # ._settings
        "FirebaseAuthSettings": "._settings",
        "settings_manager": "._settings",
        # ._utils
        "exchange_custom_token": "._utils.exchange_custom_token",
        "refresh_id_token": "._utils.refresh_id_token",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
