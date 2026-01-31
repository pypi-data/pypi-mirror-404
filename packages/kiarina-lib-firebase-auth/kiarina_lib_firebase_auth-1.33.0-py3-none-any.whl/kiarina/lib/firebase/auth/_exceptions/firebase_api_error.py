from .firebase_auth_error import FirebaseAuthError


class FirebaseAPIError(FirebaseAuthError):
    """Firebase API returned an error response."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message)

        self.status_code = status_code
        self.error_code = error_code
