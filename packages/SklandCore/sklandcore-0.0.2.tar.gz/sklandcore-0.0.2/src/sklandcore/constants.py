from enum import Enum
from typing import Final

# Hypergryph Auth URLs
HYPERGRYPH_BASE_URL: Final[str] = "https://as.hypergryph.com"
HYPERGRYPH_TOKEN_BY_PASSWORD_URL: Final[str] = (
    f"{HYPERGRYPH_BASE_URL}/user/auth/v1/token_by_phone_password"
)
HYPERGRYPH_SEND_PHONE_CODE_URL: Final[str] = f"{HYPERGRYPH_BASE_URL}/general/v1/send_phone_code"
HYPERGRYPH_TOKEN_BY_CODE_URL: Final[str] = (
    f"{HYPERGRYPH_BASE_URL}/user/auth/v2/token_by_phone_code"
)
HYPERGRYPH_OAUTH2_GRANT_URL: Final[str] = f"{HYPERGRYPH_BASE_URL}/user/oauth2/v2/grant"
HYPERGRYPH_USER_BASIC_INFO_URL: Final[str] = f"{HYPERGRYPH_BASE_URL}/user/info/v1/basic"
HYPERGRYPH_SCAN_LOGIN_URL: Final[str] = f"{HYPERGRYPH_BASE_URL}/user/info/v1/scan_login"
HYPERGRYPH_UPDATE_SCAN_STATUS_URL: Final[str] = (
    f"{HYPERGRYPH_BASE_URL}/user/info/v1/update_scan_status"
)

# Skland API URLs
SKLAND_BASE_URL: Final[str] = "https://zonai.skland.com"
SKLAND_API_BASE_URL: Final[str] = f"{SKLAND_BASE_URL}/api/v1"
SKLAND_GENERATE_CRED_URL: Final[str] = f"{SKLAND_API_BASE_URL}/user/auth/generate_cred_by_code"
SKLAND_USER_CHECK_URL: Final[str] = f"{SKLAND_API_BASE_URL}/user/check"
SKLAND_USER_INFO_URL: Final[str] = f"{SKLAND_API_BASE_URL}/user/info"
SKLAND_PLAYER_BINDING_URL: Final[str] = f"{SKLAND_API_BASE_URL}/game/player/binding"
SKLAND_PLAYER_INFO_URL: Final[str] = f"{SKLAND_API_BASE_URL}/game/player/info"
SKLAND_ATTENDANCE_URL: Final[str] = f"{SKLAND_API_BASE_URL}/game/attendance"

# Web API URLs
SKLAND_WEB_API_BASE_URL: Final[str] = "https://web-api.skland.com"
SKLAND_ACCOUNT_INFO_URL: Final[str] = f"{SKLAND_WEB_API_BASE_URL}/account/info/hg"

# Web Auth URLs (for token refresh)
SKLAND_WEB_AUTH_REFRESH_URL: Final[str] = f"{SKLAND_BASE_URL}/web/v1/auth/refresh"


class OAuth2AppCode(Enum):
    ARKNIGHTS = "7318def77669979d"
    SKLAND = "4ca99fa6b56cc2ba"
    ENDFIELD = "dd7b852d5f1dd9da"
    ENDFIELD_GAME = "4df8f5a7c2ad711b497a"

    BINDING_API = "be36d44aa36bfb5b"
    BINDING_LIST_ENDFIELD = "endfield"


# App Version
APP_VERSION: Final[str] = "1.52.1"

# Platform (1 = Android, 3 = Web)
PLATFORM: Final[str] = "1"
WEB_PLATFORM: Final[str] = "3"

# Token Refresh Settings
TOKEN_REFRESH_MAX_RETRIES: Final[int] = 3
TOKEN_REFRESH_RETRY_DELAY: Final[float] = 1.0  # seconds

# Default Headers (Android; used for AS when platform is not Windows)
HYPERGRYPH_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "Mozilla/5.0",
}

SKLAND_HEADERS: Final[dict[str, str]] = {
    "User-Agent": f"Mozilla/5.0 (Linux; Android 12; 24031PN0DC Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36; SKLand/{APP_VERSION}",  # noqa: E501
    "platform": "1",
    "vname": APP_VERSION,
}

# Web API Version (used for token refresh)
WEB_APP_VERSION: Final[str] = "1.0.0"

# Web Headers (for token refresh endpoint)
SKLAND_WEB_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; 24031PN0DC Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36; SKLand/1.52.1",  # noqa: E501
    "content-type": "application/json",
    "origin": "https://game.skland.com",
    "referer": "https://game.skland.com/",
    "accept": "*/*",
}

# Game App Codes
GAME_APP_CODE_ARKNIGHTS: Final[str] = "arknights"
GAME_APP_CODE_EXASTRIS: Final[str] = "exastris"
GAME_APP_CODE_ENDFIELD: Final[str] = "endfield"

# Channel Master IDs
CHANNEL_MASTER_ID_OFFICIAL: Final[str] = "1"  # 官服
CHANNEL_MASTER_ID_BILIBILI: Final[str] = "2"  # B服
