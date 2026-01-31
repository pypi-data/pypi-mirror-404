import asyncio
from datetime import datetime, timedelta, timezone

from .._utils.refresh_id_token import refresh_id_token
from .._schemas.token_response import TokenResponse


class TokenManager:
    def __init__(
        self,
        refresh_token: str,
        api_key: str,
        *,
        id_token: str | None = None,
        expires_at: datetime | None = None,
        refresh_buffer_seconds: int = 300,
    ):
        self.refresh_token: str = refresh_token
        self.api_key: str = api_key
        self._id_token: str | None = id_token
        self._expires_at: datetime | None = expires_at
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._refresh_lock = asyncio.Lock()

    @property
    def id_token(self) -> str:
        if self._id_token is None:  # pragma: no cover
            raise AssertionError("ID token is not set.")

        return self._id_token

    @property
    def expires_at(self) -> datetime:
        if self._expires_at is None:  # pragma: no cover
            raise AssertionError("Expiration time is not set.")

        return self._expires_at

    async def get_id_token(self) -> str:
        if self._needs_refresh():
            async with self._refresh_lock:
                # Double-check after acquiring lock
                if self._needs_refresh():
                    await self._do_refresh()

        assert self._id_token is not None
        return self._id_token

    async def refresh(self) -> TokenResponse:
        async with self._refresh_lock:
            return await self._do_refresh()

    def _needs_refresh(self) -> bool:
        if self._id_token is None or self._expires_at is None:
            return True

        now = datetime.now(timezone.utc)
        refresh_threshold = self._expires_at - timedelta(
            seconds=self._refresh_buffer_seconds
        )

        return now >= refresh_threshold

    async def _do_refresh(self) -> TokenResponse:
        response = await refresh_id_token(self.refresh_token, self.api_key)

        self.refresh_token = response.refresh_token
        self._id_token = response.id_token
        self._expires_at = response.expires_at

        return response
