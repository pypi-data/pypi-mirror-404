from .firebase_auth_error import FirebaseAuthError


class InvalidRefreshTokenError(FirebaseAuthError):
    """Refresh token is invalid or expired."""

    pass
