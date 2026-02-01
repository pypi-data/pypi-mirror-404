import asyncio

import httpx

from ..constants import (
    SKLAND_GENERATE_CRED_URL,
    SKLAND_HEADERS,
    SKLAND_USER_CHECK_URL,
    SKLAND_WEB_AUTH_REFRESH_URL,
    SKLAND_WEB_HEADERS,
    TOKEN_REFRESH_MAX_RETRIES,
    TOKEN_REFRESH_RETRY_DELAY,
)
from ..exceptions import AuthenticationError, InvalidCredentialError, NetworkError
from ..models.auth import SKlandCredential, TokenRefreshData, UserCheckData
from ..models.base import SklandResponse
from ..signature import get_signed_headers, get_web_signed_headers


class SklandAuth:
    def __init__(self, http_client: httpx.AsyncClient, device_id: str):
        self._http = http_client
        self._device_id = device_id

    async def generate_cred_by_code(self, code: str) -> SKlandCredential:
        """Generate Skland credential from OAuth2 grant code.

        Args:
            code: OAuth2 grant code from Hypergryph

        Returns:
            Credential containing cred and token for API access

        Raises:
            AuthenticationError: If credential generation fails
            NetworkError: If network error occurs
        """
        try:
            response = await self._http.post(
                SKLAND_GENERATE_CRED_URL,
                headers=SKLAND_HEADERS,
                json={"code": code, "kind": 1},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error generating cred: {e}") from e

        result = SklandResponse[SKlandCredential].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.message, code=result.code)

        return result.data

    async def check_cred(
        self,
        cred: str,
        token: str,
    ) -> UserCheckData:
        """Check if credential is valid.

        Args:
            cred: Credential token
            token: Sign token for request signature

        Returns:
            User check data

        Raises:
            InvalidCredentialError: If credential is invalid or expired
            NetworkError: If network error occurs
        """
        headers = get_signed_headers(
            url=SKLAND_USER_CHECK_URL,
            method="GET",
            body=None,
            base_headers=SKLAND_HEADERS,
            sign_token=token,
            cred=cred,
            device_id=self._device_id,
        )

        try:
            response = await self._http.get(
                SKLAND_USER_CHECK_URL,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error checking cred: {e}") from e

        result = SklandResponse[UserCheckData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            if "用户未登录" in result.message or result.code == 10001:
                raise InvalidCredentialError(result.message, code=result.code)
            raise AuthenticationError(result.message, code=result.code)

        return result.data

    async def refresh_cred(self, code: str) -> SKlandCredential:
        """Refresh credential using a new grant code.

        This is an alias for generate_cred_by_code, as Skland
        doesn't have a separate refresh endpoint.

        Args:
            code: New OAuth2 grant code from Hypergryph

        Returns:
            New credential

        Raises:
            AuthenticationError: If credential generation fails
            NetworkError: If network error occurs
        """
        return await self.generate_cred_by_code(code)

    async def _refresh_token_once(self, cred: str, old_token: str) -> str:
        """Attempt to refresh token once.

        Args:
            cred: Current credential

        Returns:
            New token string

        Raises:
            InvalidCredentialError: If token is expired (code 10000)
            AuthenticationError: If refresh fails
            NetworkError: If network error occurs
        """
        headers = get_web_signed_headers(
            url=SKLAND_WEB_AUTH_REFRESH_URL,
            method="GET",
            body=None,
            base_headers=SKLAND_WEB_HEADERS,
            old_token=old_token,
            cred=cred,
            device_id=self._device_id,
        )

        try:
            response = await self._http.get(
                SKLAND_WEB_AUTH_REFRESH_URL,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error refreshing token: {e}") from e

        result = SklandResponse[TokenRefreshData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            # Code 10000: Token expired, needs re-authentication
            # Code 10001: Invalid device info
            if result.code == 10000:
                raise InvalidCredentialError(
                    "Token expired, re-authentication required",
                    code=result.code,
                )
            if result.code == 10001:
                raise InvalidCredentialError(
                    "Invalid device info",
                    code=result.code,
                )
            raise AuthenticationError(result.message, code=result.code)

        return result.data.token

    async def refresh_token(
        self,
        cred: str,
        old_token: str,
        max_retries: int = TOKEN_REFRESH_MAX_RETRIES,
        retry_delay: float = TOKEN_REFRESH_RETRY_DELAY,
    ) -> str:
        """Refresh token with internal retry logic.

        Attempts to refresh the token multiple times before raising an exception.
        Only raises exception after all retries are exhausted.

        Args:
            cred: Current credential
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)

        Returns:
            New token string

        Raises:
            InvalidCredentialError: If token is expired after all retries
            AuthenticationError: If refresh fails after all retries
            NetworkError: If network error persists after all retries
        """
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                return await self._refresh_token_once(cred, old_token)
            except InvalidCredentialError:
                # Token expired, no point retrying with same credentials
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        # All retries exhausted
        if last_error is not None:
            raise last_error
        raise AuthenticationError("Token refresh failed after all retries")
