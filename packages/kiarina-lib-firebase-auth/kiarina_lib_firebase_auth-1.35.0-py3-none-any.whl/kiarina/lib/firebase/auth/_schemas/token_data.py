from datetime import datetime, timedelta, timezone

from pydantic import BaseModel


class TokenData(BaseModel):
    """Firebase authentication token data."""

    refresh_token: str
    """Refresh token for getting new ID tokens."""

    id_token: str
    """Firebase ID token (JWT)."""

    expires_at: datetime
    """ID token expiration time (UTC)."""

    @classmethod
    def from_api_response(
        cls,
        id_token: str,
        refresh_token: str,
        expires_in: int,
        *,
        issued_at: datetime | None = None,
    ) -> "TokenData":
        """
        Create TokenData from Firebase API response.

        Args:
            id_token: Firebase ID token
            refresh_token: Refresh token
            expires_in: Token lifetime in seconds
            issued_at: Token issue time (defaults to now)
        """
        if issued_at is None:
            issued_at = datetime.now(timezone.utc)

        return cls(
            refresh_token=refresh_token,
            id_token=id_token,
            expires_at=issued_at + timedelta(seconds=expires_in),
        )
