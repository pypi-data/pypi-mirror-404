from typing import Protocol

from .._schemas.token_data import TokenData


class TokenDataCache(Protocol):
    """
    Protocol for token data cache implementations.

    Implementations should provide persistent storage for TokenData,
    allowing TokenManager to automatically save and restore token state.
    """

    async def get(self) -> TokenData:
        """
        Retrieve cached token data.

        Returns:
            TokenData: Cached token data

        Raises:
            Exception: If token data cannot be retrieved
        """
        ...

    async def set(self, token_data: TokenData) -> None:
        """
        Store token data in cache.

        Args:
            token_data: Token data to cache

        Raises:
            Exception: If token data cannot be stored
        """
        ...
