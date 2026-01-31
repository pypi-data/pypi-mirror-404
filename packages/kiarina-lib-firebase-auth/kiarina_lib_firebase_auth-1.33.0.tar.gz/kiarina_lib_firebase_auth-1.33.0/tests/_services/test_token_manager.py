import asyncio

import pytest

from kiarina.lib.firebase.auth import (
    TokenManager,
    exchange_custom_token,
    settings_manager,
)


async def test_token_manager(firebase_app):
    auth = pytest.importorskip("firebase_admin.auth")
    custom_token = auth.create_custom_token("test").decode("utf-8")

    settings = settings_manager.get_settings()
    api_key = settings.api_key.get_secret_value()

    response = await exchange_custom_token(
        custom_token=custom_token,
        api_key=api_key,
    )

    manager = TokenManager(
        refresh_token=response.refresh_token,
        api_key=api_key,
    )

    id_token = await manager.get_id_token()
    expires_at = manager.expires_at
    assert id_token == manager.id_token

    id_token_2 = await manager.get_id_token()
    assert id_token_2 == id_token
    assert manager.expires_at == expires_at

    await asyncio.sleep(0.1)

    await manager.refresh()
    assert manager.expires_at > expires_at
