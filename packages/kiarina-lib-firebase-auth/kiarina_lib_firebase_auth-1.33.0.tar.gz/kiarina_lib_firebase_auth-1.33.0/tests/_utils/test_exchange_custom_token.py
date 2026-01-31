import httpx
import pytest

from kiarina.lib.firebase.auth import (
    FirebaseAPIError,
    InvalidCustomTokenError,
    exchange_custom_token,
    settings_manager,
)


async def test_invalid_custom_token(load_settings) -> None:
    settings = settings_manager.get_settings()

    with pytest.raises(InvalidCustomTokenError):
        await exchange_custom_token(
            custom_token="invalid_custom_token",
            api_key=settings.api_key.get_secret_value(),
        )


async def test_firebase_api_error() -> None:
    with pytest.raises(FirebaseAPIError):
        await exchange_custom_token(
            custom_token="invalid_custom_token",
            api_key="invalid_api_key",
        )


async def test_httpx_reqest_error(monkeypatch) -> None:
    def mock_post(*args, **kwargs):
        raise httpx.RequestError("Network error")

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    with pytest.raises(FirebaseAPIError) as exc_info:
        await exchange_custom_token(
            custom_token="some_custom_token",
            api_key="invalid_api_key",
        )

    assert "Request failed" in str(exc_info.value)


async def test_happy_path(firebase_app) -> None:
    auth = pytest.importorskip("firebase_admin.auth")

    custom_token = auth.create_custom_token("test").decode("utf-8")

    settings = settings_manager.get_settings()
    response = await exchange_custom_token(
        custom_token=custom_token,
        api_key=settings.api_key.get_secret_value(),
    )

    assert response.id_token
    assert response.refresh_token
    assert response.expires_in > 0
