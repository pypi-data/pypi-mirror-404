from .did_manager import get_or_create_did
from .exceptions import (
    AlreadySignedError,
    AuthenticationError,
    GameNotBoundError,
    InvalidCredentialError,
    LoginError,
    NetworkError,
    PlayerNotFoundError,
    RateLimitError,
    RequestError,
    ServerError,
    SignatureError,
    SklandError,
)
from .models import (
    AttendanceAward,
    AttendanceData,
    AttendanceResource,
    BindingData,
    BindingRole,
    Character,
    CharacterEquip,
    CharacterSkill,
    GameBinding,
    GrantCodeDataType0,
    HypergryphResponse,
    HypergryphTokenData,
    PlayerData,
    PlayerStatus,
    ScanLoginAppInfo,
    SKlandCredential,
    SklandResponse,
    UserBasicInfo,
    UserCheckData,
)
from .skd_client import SklandClient
from .wechat_qecode.qrcode import (
    QRCodeDetectorInitError,
    QRCodeError,
    QRCodeNotFoundError,
    ScanIdNotFoundError,
    detect_qrcode,
    extract_scan_id,
    extract_scan_id_from_image,
)

__version__ = "0.0.1"

__all__ = [  # noqa: RUF022
    # Main client
    "SklandClient",
    # DID manager
    "get_or_create_did",
    # Exceptions
    "SklandError",
    "AuthenticationError",
    "InvalidCredentialError",
    "LoginError",
    "RequestError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "PlayerNotFoundError",
    "GameNotBoundError",
    "AlreadySignedError",
    "SignatureError",
    # QR Code exceptions
    "QRCodeError",
    "QRCodeDetectorInitError",
    "QRCodeNotFoundError",
    "ScanIdNotFoundError",
    # QR Code functions
    "detect_qrcode",
    "extract_scan_id",
    "extract_scan_id_from_image",
    # Response models
    "HypergryphResponse",
    "SklandResponse",
    # Auth models
    "SKlandCredential",
    "GrantCodeDataType0",
    "HypergryphTokenData",
    "ScanLoginAppInfo",
    "UserBasicInfo",
    "UserCheckData",
    # Game models
    "AttendanceAward",
    "AttendanceData",
    "AttendanceResource",
    "BindingData",
    "BindingRole",
    "Character",
    "CharacterEquip",
    "CharacterSkill",
    "GameBinding",
    "PlayerData",
    "PlayerStatus",
]
