import asyncio
from datetime import datetime, timedelta, timezone

from .._schemas.token_data import TokenData
from .._utils.refresh_id_token import refresh_id_token


class TokenManager:
    """
    Service class for automatic ID token lifecycle management.

    Automatically refreshes ID tokens before expiration with thread-safe operations.
    """

    def __init__(
        self,
        *,
        api_key: str,
        refresh_token: str | None = None,
        token_data: TokenData | None = None,
        refresh_buffer_seconds: int = 300,
    ):
        if not refresh_token:
            if not token_data:
                raise ValueError(
                    "Either 'refresh_token' or 'token_data' must be provided."
                )

            refresh_token = token_data.refresh_token

        self.api_key: str = api_key
        self.refresh_token: str = refresh_token
        self._token_data: TokenData | None = token_data
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._refresh_lock = asyncio.Lock()

    @property
    def token_data(self) -> TokenData:
        if not self._token_data:
            raise AssertionError("Token data is not set.")

        return self._token_data

    @property
    def id_token(self) -> str:
        return self.token_data.id_token

    @property
    def expires_at(self) -> datetime:
        return self.token_data.expires_at

    async def get_id_token(self) -> str:
        """
        Get current ID token (auto-refreshes if needed).
        """
        if self._needs_refresh():
            async with self._refresh_lock:
                # Double-check after acquiring lock
                if self._needs_refresh():
                    await self._do_refresh()

        return self.id_token

    async def refresh(self) -> TokenData:
        """
        Manually refresh ID token.
        """
        async with self._refresh_lock:
            return await self._do_refresh()

    def _needs_refresh(self) -> bool:
        if not self._token_data:
            return True

        now = datetime.now(timezone.utc)
        refresh_threshold = self.expires_at - timedelta(
            seconds=self._refresh_buffer_seconds
        )

        return now >= refresh_threshold

    async def _do_refresh(self) -> TokenData:
        token_data = await refresh_id_token(self.refresh_token, self.api_key)

        self.refresh_token = token_data.refresh_token
        self._token_data = token_data

        return token_data
