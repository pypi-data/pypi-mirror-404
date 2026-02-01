import httpx

from sklandcore.constants import OAuth2AppCode
from sklandcore.exceptions import AuthenticationError, NetworkError
from sklandcore.models.u8 import TokenByChannelTokenData, U8GrantCodeData, U8Response

# U8 API URL
U8_TOKEN_BY_CHANNEL_TOKEN_URL = "https://u8.hypergryph.com/u8/user/auth/v2/token_by_channel_token"
U8_GET_GRANT_CODE_URL = "https://u8.hypergryph.com/u8/user/auth/v2/grant"


class U8Auth:
    """U8 authentication handler for Beyond/Endfield games.

    U8 is Hypergryph's authentication service for game clients.
    This class handles the final step of the authentication flow,
    converting OAuth2 grant codes into game-specific tokens.
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """Initialize U8Auth.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    async def token_by_channel_token(
        self,
        app_code: OAuth2AppCode,
        channel_master_id: str,
        channel_token: str,
        platform: int,
    ) -> TokenByChannelTokenData:
        """Exchange channel token for game authentication token.

        This is the final step in the Beyond/Endfield authentication flow.
        It takes the OAuth2 grant code (wrapped in channelToken JSON) and
        returns a game-specific authentication token.

        Args:
            app_code: OAuth2 application code (e.g., OAuth2AppCode.ENDFIELD)
            channel_master_id: Channel ID for the game server.
                - "1" = Official server (官服)
                - "2" = Bilibili server (B服)
            channel_token: JSON string containing the OAuth2 grant code.
                Format: {"code": "<grant_code>", "type": 1, "isSuc": true}
            platform: Platform identifier for the client.
                - 0 = Android
                - 1 = iOS
                - 2 = Windows

        Returns:
            TokenByChannelTokenData containing:
                - token: Game authentication token
                - uid: User ID
                - isNew: Whether this is a new user

        Raises:
            AuthenticationError: If authentication fails (invalid code, etc.)
            NetworkError: If network error occurs during request
        """
        try:
            response = await self._http.post(
                U8_TOKEN_BY_CHANNEL_TOKEN_URL,
                json={
                    "appCode": app_code.value,
                    "channelMasterId": channel_master_id,
                    "channelToken": channel_token,
                    "type": 0,
                    "platform": platform,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error during login: {e}") from e

        result = U8Response[TokenByChannelTokenData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def get_grant_code(self, token: str, type: int, platform: int) -> U8GrantCodeData:
        """Get grant code from U8."""
        try:
            response = await self._http.post(
                U8_GET_GRANT_CODE_URL,
                json={
                    "token": token,
                    "type": type,
                    "platform": platform,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting grant code: {e}") from e

        result = U8Response[U8GrantCodeData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data
