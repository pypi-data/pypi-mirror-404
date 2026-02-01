from .firebase_auth_error import FirebaseAuthError


class InvalidCustomTokenError(FirebaseAuthError):
    """Custom token is invalid or expired."""

    pass
