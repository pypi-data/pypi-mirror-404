import asyncio

import pytest

from kiarina.lib.firebase.auth import (
    TokenManager,
    exchange_custom_token,
    settings_manager,
)


async def test_missing_parameters():
    with pytest.raises(ValueError, match="Either 'refresh_token' or 'token_data'"):
        TokenManager(api_key="test")


async def test_happy_path(custom_token):
    settings = settings_manager.get_settings()
    api_key = settings.api_key.get_secret_value()

    token_data = await exchange_custom_token(
        custom_token=custom_token,
        api_key=api_key,
    )

    # check both initialization methods
    manager = TokenManager(
        api_key=api_key,
        token_data=token_data,
    )

    manager = TokenManager(
        api_key=api_key,
        refresh_token=token_data.refresh_token,
    )

    with pytest.raises(AssertionError, match="Token data is not set."):
        manager.token_data

    id_token = await manager.get_id_token()
    expires_at = manager.expires_at
    assert id_token == manager.id_token

    id_token_2 = await manager.get_id_token()
    assert id_token_2 == id_token
    assert manager.expires_at == expires_at

    await asyncio.sleep(0.1)

    new_token_data = await manager.refresh()
    assert manager.expires_at > expires_at
    assert new_token_data.expires_at == manager.expires_at
