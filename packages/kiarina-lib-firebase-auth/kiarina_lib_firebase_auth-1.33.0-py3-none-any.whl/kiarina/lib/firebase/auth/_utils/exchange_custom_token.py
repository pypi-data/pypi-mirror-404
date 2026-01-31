import httpx

from .._exceptions.firebase_api_error import FirebaseAPIError
from .._exceptions.invalid_custom_token_error import InvalidCustomTokenError
from .._schemas.token_response import TokenResponse


async def exchange_custom_token(custom_token: str, api_key: str) -> TokenResponse:
    """
    Exchange a Firebase custom token for an ID token.

    Raises:
        InvalidCustomTokenError: If the custom token is invalid
        FirebaseAPIError: If Firebase API returns an error
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"

    payload = {
        "token": custom_token,
        "returnSecureToken": True,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            error_code = error_data.get("error", {}).get("code")

            # Check for invalid custom token error
            if "INVALID_CUSTOM_TOKEN" in error_message:
                raise InvalidCustomTokenError(
                    f"Invalid custom token: {error_message}"
                ) from e

            raise FirebaseAPIError(
                message=f"Firebase API error: {error_message}",
                status_code=e.response.status_code,
                error_code=error_code,
            ) from e

        except httpx.RequestError as e:
            raise FirebaseAPIError(f"Request failed: {e}") from e

    data = response.json()

    return TokenResponse(
        id_token=data["idToken"],
        refresh_token=data["refreshToken"],
        expires_in=int(data["expiresIn"]),
    )
