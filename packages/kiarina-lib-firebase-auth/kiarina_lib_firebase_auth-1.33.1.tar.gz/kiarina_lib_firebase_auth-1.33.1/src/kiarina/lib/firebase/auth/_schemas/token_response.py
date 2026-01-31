from datetime import datetime, timedelta, timezone

from pydantic import BaseModel


class TokenResponse(BaseModel):
    id_token: str
    """Firebase ID token (JWT)."""

    refresh_token: str
    """Refresh token for getting new ID tokens."""

    expires_in: int
    """ID token lifetime in seconds."""

    @property
    def expires_at(self) -> datetime:
        """
        Calculate expiration datetime (UTC).
        """
        return datetime.now(timezone.utc) + timedelta(seconds=self.expires_in)
