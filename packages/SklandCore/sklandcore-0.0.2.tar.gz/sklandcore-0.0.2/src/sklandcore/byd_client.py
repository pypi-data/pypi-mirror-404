import json
from copy import deepcopy
from typing import final

import httpx

from sklandcore.auth.hypergryph import HypergryphAuth
from sklandcore.auth.u8 import U8Auth
from sklandcore.constants import (
    CHANNEL_MASTER_ID_OFFICIAL,
    HYPERGRYPH_HEADERS,
    OAuth2AppCode,
)
from sklandcore.exceptions import AuthenticationError
from sklandcore.models.auth import (
    BeyondCredential,
    BindingListData,
    CheckScanLoginStatusSuccessData,
    GenerateScanLoginData,
    GrantCodeDataType0,
    GrantCodeDataType1BindingAPI,
)
from sklandcore.models.u8 import TokenByChannelTokenData
from sklandcore.platform import (
    HypergryphDevice,
    HypergryphDeviceAndroid,
    HypergryphDeviceWindows,
    PlatformEnum,
)


@final
class BeyondClient:
    """Client for Beyond/Endfield game authentication.

    Supports three login methods:
    - Password login (requires user-provided deviceToken)
    - SMS code login (deviceToken obtained automatically)
    - QR code scan login (deviceToken obtained automatically)

    Authentication flow:
    1. Get account token (and deviceToken) via Hypergryph API
    2. Get grant code via OAuth2 grant API
    3. Get final token via U8 token_by_channel_token API
    4. Get grant code via U8 API
    5. Build and store credential
    6. Return credential

    Raises:
        AuthenticationError: If authentication fails
        NetworkError: If network error occurs
    """

    def __init__(self, device: HypergryphDevice):
        """Initialize BeyondClient.

        Args:
            device: Hypergryph device
        """
        # self._phone = phone
        self._device = device
        self._initialized = False
        self._code: str | None = None
        self._token: str | None = None
        self._grant_token: str | None = None
        self._uid: str | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client and auth instances."""
        if self._initialized:
            return
        self._initialized = True

        as_headers = None
        if isinstance(self._device, HypergryphDeviceWindows):
            as_headers = deepcopy(HYPERGRYPH_HEADERS)
            as_headers["X-DeviceId"] = self._device.device_id
            as_headers["X-DeviceId2"] = self._device.device_id2
            as_headers["X-DeviceModel"] = self._device.device_model
            as_headers["X-DeviceType"] = str(self._device.device_type.value)
        elif isinstance(self._device, HypergryphDeviceAndroid):
            as_headers = deepcopy(HYPERGRYPH_HEADERS)
            as_headers["did"] = self._device.did
        else:
            raise ValueError(f"Unsupported device type: {self._device}")

        self._http = httpx.AsyncClient(timeout=30.0)
        self._hypergryph_auth = HypergryphAuth(http_client=self._http, headers=as_headers)
        self._u8_auth = U8Auth(http_client=self._http)

    async def close(self) -> None:
        """Close HTTP client."""
        if self._initialized and hasattr(self, "_http"):
            await self._http.aclose()

    @property
    def code(self) -> str | None:
        """Get current credential."""
        return self._code

    @property
    def token(self) -> str | None:
        """Get current token."""
        return self._token

    @property
    def uid(self) -> str | None:
        """Get current user ID."""
        return self._uid

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._code is not None and self._token is not None

    def _build_channel_token(self, grant_code: str) -> str:
        """Build channelToken JSON string for U8 API.

        Args:
            grant_code: Grant code from OAuth2 grant API

        Returns:
            JSON string in format: {"code":"...", "type":1, "isSuc":true}
        """
        return json.dumps(
            {"code": grant_code, "type": 1, "isSuc": True},
            separators=(",", ":"),
        )

    async def _complete_login(
        self,
        account_token: str,
        device_token: str,
        platform: PlatformEnum = PlatformEnum.WINDOWS,
        use_binding_api: bool = False,
    ) -> BeyondCredential:
        """Complete login flow with steps 2 and 3.

        Args:
            account_token: Token from step 1 (password/code/scan login)
            device_token: Device token for OAuth2 grant
            platform: Platform identifier (ANDROID, IOS, WINDOWS)

        Returns:
            Credential with cred, token, and userId

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network error occurs
        """
        if use_binding_api:
            # Step 2: Get grant code via OAuth2 grant API
            binding_grant_data = await self._hypergryph_auth.get_grant_code(
                app_code=OAuth2AppCode.BINDING_API,
                token=account_token,
                device_token=device_token,
                type=1,
            )
            assert isinstance(binding_grant_data, GrantCodeDataType1BindingAPI)

            # Step 3: Get binding list via Binding API to get Endfield UID
            binding_list_data: BindingListData = await self._hypergryph_auth.get_binding_list(
                token=binding_grant_data.token,
                app_code=OAuth2AppCode.BINDING_LIST_ENDFIELD,
            )

            # Step 4: Get final token via Binding API
            binding_data = await self._hypergryph_auth.get_u8_token_by_uid(
                uid=binding_list_data.list[0].bindingList[0].uid,
                token=binding_grant_data.token,
            )

            credential = BeyondCredential(
                code="",
                token=binding_data.token,
                grantToken=binding_grant_data.token,
                userId=binding_list_data.list[0].bindingList[0].uid,
            )

            self._code = credential.code
            self._token = credential.token
            self._grant_token = credential.grantToken
            self._uid = credential.userId

            return credential
        else:
            # Step 2: Get grant code via OAuth2 grant API
            grant_data = await self._hypergryph_auth.get_grant_code(
                app_code=OAuth2AppCode.ENDFIELD,
                token=account_token,
                device_token=device_token,
                type=0,
            )

            assert isinstance(grant_data, GrantCodeDataType0)

            # Step 3: Build channelToken and get final token via U8 API
            channel_token = self._build_channel_token(grant_data.code)
            token_data: TokenByChannelTokenData = await self._u8_auth.token_by_channel_token(
                app_code=OAuth2AppCode.ENDFIELD_GAME,
                channel_master_id=CHANNEL_MASTER_ID_OFFICIAL,
                channel_token=channel_token,
                platform=platform,
            )

            # Step 4: Get grant code via U8 API
            grant_data = await self._u8_auth.get_grant_code(
                token=token_data.token,
                type=0,
                platform=platform,
            )

            # Build and store credential
            credential = BeyondCredential(
                code=grant_data.code,
                token=token_data.token,
                grantToken=grant_data.token,
                userId=grant_data.uid,
            )

            self._code = credential.code
            self._token = credential.token
            self._grant_token = credential.grantToken
            self._uid = credential.userId
            return credential

    async def send_phone_code(self, phone: str) -> bool:
        """Send SMS verification code to phone.

        Returns:
            True if code sent successfully

        Raises:
            AuthenticationError: If sending fails
            NetworkError: If network error occurs
        """
        return await self._hypergryph_auth.send_phone_code(phone)

    async def login_by_password(
        self,
        phone: str,
        password: str,
        device_token: str,
        platform: PlatformEnum = PlatformEnum.WINDOWS,
        use_binding_api: bool = False,
    ) -> BeyondCredential:
        """Login by phone and password.

        Note: Password login only returns token without deviceToken,
        so deviceToken must be provided by the caller.

        Args:
            password: Account password
            device_token: Device token (must be provided by user)
            platform: Platform identifier (ANDROID, IOS, WINDOWS)

        Returns:
            Credential with cred, token, and userId

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network error occurs
        """
        if not device_token:
            raise AuthenticationError("device_token is required for password login")

        # Step 1: Get account token via password login
        account_token_data = await self._hypergryph_auth.login_by_password(phone, password)

        # Steps 2 & 3: Complete login flow
        return await self._complete_login(
            account_token=account_token_data.token,
            device_token=device_token,
            platform=platform,
            use_binding_api=use_binding_api,
        )

    async def login_by_code(
        self,
        phone: str,
        code: str,
        platform: PlatformEnum = PlatformEnum.WINDOWS,
        use_binding_api: bool = False,
    ) -> BeyondCredential:
        """Login by phone and SMS verification code.

        Note: Code login returns both token and deviceToken automatically.

        Args:
            code: SMS verification code
            platform: Platform identifier (ANDROID, IOS, WINDOWS)

        Returns:
            Credential with cred, token, and userId

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network error occurs
        """
        # Step 1: Get account token and deviceToken via code login
        account_token_data = await self._hypergryph_auth.login_by_code(
            app_code=OAuth2AppCode.ENDFIELD,
            phone=phone,
            code=code,
        )

        # Steps 2 & 3: Complete login flow
        return await self._complete_login(
            account_token=account_token_data.token,
            device_token=account_token_data.deviceToken,
            platform=platform,
            use_binding_api=use_binding_api,
        )

    async def generate_scan_login(self) -> GenerateScanLoginData:
        """Generate scan login (get scanId and scanUrl).

        Returns:
            GenerateScanLoginData with scanId and scanUrl

        Raises:
            AuthenticationError: If generation fails
            NetworkError: If network error occurs
        """
        return await self._hypergryph_auth.generate_scan_login()

    async def check_scan_login_status(
        self, scan_id: str
    ) -> CheckScanLoginStatusSuccessData | str:
        """Check scan login status.

        Args:
            scan_id: Scan ID from QR code

        Returns:
            Status string: "未扫码", "已扫码待确认", "已失效"
            Or CheckScanLoginStatusSuccessData when confirmed

        Raises:
            AuthenticationError: If checking fails
            NetworkError: If network error occurs
        """
        return await self._hypergryph_auth.check_scan_login_status(scan_id=scan_id)

    async def complete_scan_login(
        self,
        scan_code: str,
        platform: PlatformEnum = PlatformEnum.WINDOWS,
        use_binding_api: bool = False,
    ) -> BeyondCredential:
        """Complete scan login after user confirms QR code.

        Args:
            scan_code: Scan code from confirmed QR code

        Returns:
            Credential with cred, token, and userId

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network error occurs
        """
        # Step 1: Get account token and deviceToken via scan login
        account_token_data = await self._hypergryph_auth.token_by_scan_code(
            appCode=OAuth2AppCode.ENDFIELD,
            from_=0,
            scan_code=scan_code,
        )

        # Steps 2 & 3: Complete login flow
        return await self._complete_login(
            account_token=account_token_data.token,
            device_token=account_token_data.deviceToken,
            platform=platform,
            use_binding_api=use_binding_api,
        )

    def set_credential(self, cred: str, token: str, uid: str | None = None) -> None:
        """Manually set credential.

        Args:
            cred: Credential string
            token: Token string
            uid: User ID (optional)
        """
        self._cred = cred
        self._token = token
        self._uid = uid

    async def __aenter__(self) -> "BeyondClient":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
