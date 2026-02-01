import asyncio
from datetime import datetime, timedelta, timezone

from .._schemas.token_data import TokenData
from .._types.token_data_cache import TokenDataCache
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
        token_data_cache: TokenDataCache | None = None,
        refresh_buffer_seconds: int = 300,
    ):
        # Validate that at least one token source is provided
        if not refresh_token and not token_data and not token_data_cache:
            raise ValueError(
                "At least one of 'refresh_token', 'token_data', or 'token_data_cache' must be provided."
            )

        self.api_key: str = api_key
        self._refresh_token: str | None = refresh_token
        self._token_data: TokenData | None = token_data
        self._token_data_cache: TokenDataCache | None = token_data_cache
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._refresh_lock = asyncio.Lock()

        if not self._refresh_token and token_data:
            self._refresh_token = token_data.refresh_token

    @property
    def refresh_token(self) -> str:
        if not self._refresh_token:
            raise AssertionError("Refresh token is not set. Call get_id_token() first.")

        return self._refresh_token

    @property
    def token_data(self) -> TokenData:
        if not self._token_data:
            raise AssertionError("Token data is not set. Call get_id_token() first.")

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
        # Load from cache if needed
        if not self._token_data and self._token_data_cache:
            async with self._refresh_lock:
                if self._token_data is None:
                    self._token_data = await self._token_data_cache.get()
                    self._refresh_token = self._token_data.refresh_token

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

        self._refresh_token = token_data.refresh_token
        self._token_data = token_data

        if self._token_data_cache:
            await self._token_data_cache.set(token_data)

        return token_data
