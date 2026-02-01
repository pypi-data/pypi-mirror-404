import httpx

from ..constants import (
    HYPERGRYPH_OAUTH2_GRANT_URL,
    HYPERGRYPH_SCAN_LOGIN_URL,
    HYPERGRYPH_SEND_PHONE_CODE_URL,
    HYPERGRYPH_TOKEN_BY_CODE_URL,
    HYPERGRYPH_TOKEN_BY_PASSWORD_URL,
    HYPERGRYPH_UPDATE_SCAN_STATUS_URL,
    HYPERGRYPH_USER_BASIC_INFO_URL,
    OAuth2AppCode,
)
from ..exceptions import AuthenticationError, LoginError, NetworkError
from ..models.auth import (
    BindingListData,
    CheckScanLoginStatusSuccessData,
    GenerateScanLoginData,
    GrantCodeDataType0,
    GrantCodeDataType1,
    GrantCodeDataType1BindingAPI,
    HypergryphTokenData,
    ScanLoginAppInfo,
    TokenByPasswordData,
    U8TokenByUidData,
    UserBasicInfo,
)
from ..models.base import BindingAPIResponse, HypergryphResponse


class HypergryphAuth:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        headers: dict[str, str],
    ):
        self._http = http_client
        self._headers = headers

    async def login_by_password(self, phone: str, password: str) -> TokenByPasswordData:
        """使用手机号和密码登录"""
        try:
            response = await self._http.post(
                HYPERGRYPH_TOKEN_BY_PASSWORD_URL,
                headers=self._headers,
                json={"phone": phone, "password": password},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error during login: {e}") from e

        result = HypergryphResponse[TokenByPasswordData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise LoginError(result.msg, code=result.status)

        return result.data

    async def send_phone_code(self, phone: str) -> bool:
        """发送手机验证码"""
        try:
            response = await self._http.post(
                HYPERGRYPH_SEND_PHONE_CODE_URL,
                headers=self._headers,
                json={"phone": phone, "type": 2},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error sending code: {e}") from e

        result = HypergryphResponse[None].model_validate_json(response.content)

        if not result.is_success():
            raise AuthenticationError(result.msg, code=result.status)

        return True

    async def login_by_code(
        self, app_code: OAuth2AppCode, phone: str, code: str
    ) -> HypergryphTokenData:
        """使用手机号和验证码登录"""
        try:
            response = await self._http.post(
                HYPERGRYPH_TOKEN_BY_CODE_URL,
                headers=self._headers,
                json={"phone": phone, "code": code, "appCode": app_code.value},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error during login: {e}") from e

        result = HypergryphResponse[HypergryphTokenData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise LoginError(result.msg, code=result.status)

        return result.data

    async def get_grant_code(
        self, app_code: OAuth2AppCode, token: str, device_token: str, type: int
    ) -> GrantCodeDataType0 | GrantCodeDataType1 | GrantCodeDataType1BindingAPI:
        """获取授权码"""
        try:
            match type:
                case 0:
                    response = await self._http.post(
                        HYPERGRYPH_OAUTH2_GRANT_URL,
                        headers=self._headers,
                        json={
                            "token": token,
                            "deviceToken": device_token,
                            "appCode": app_code.value,
                            "type": 0,
                        },
                    )
                case 1:
                    response = await self._http.post(
                        HYPERGRYPH_OAUTH2_GRANT_URL,
                        headers=self._headers,
                        json={
                            "token": token,
                            "appCode": app_code.value,
                            "type": 1,
                        },
                    )
                case _:
                    raise AuthenticationError("Invalid type for getting grant code")
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting grant code: {e}") from e

        match (type, app_code):
            case (0, _):
                result = HypergryphResponse[GrantCodeDataType0].model_validate_json(
                    response.content
                )
            case (1, OAuth2AppCode.BINDING_API):
                result = HypergryphResponse[GrantCodeDataType1BindingAPI].model_validate_json(
                    response.content
                )
            case (1, _):
                result = HypergryphResponse[GrantCodeDataType1].model_validate_json(
                    response.content
                )
            case _:
                raise AuthenticationError("Invalid type for getting grant code")

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def get_user_basic_info(self, token: str) -> UserBasicInfo:
        """获取用户基本信息"""
        try:
            response = await self._http.get(
                HYPERGRYPH_USER_BASIC_INFO_URL,
                headers=self._headers,
                params={"token": token},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting user info: {e}") from e

        result = HypergryphResponse[UserBasicInfo].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def scan_login(self, token: str, scan_id: str) -> ScanLoginAppInfo:
        try:
            response = await self._http.post(
                HYPERGRYPH_SCAN_LOGIN_URL,
                headers=self._headers,
                json={"token": token, "scanId": scan_id},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error during scan login: {e}") from e

        result = HypergryphResponse[ScanLoginAppInfo].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def update_scan_status(self, token: str, scan_id: str) -> bool:
        try:
            response = await self._http.post(
                HYPERGRYPH_UPDATE_SCAN_STATUS_URL,
                headers=self._headers,
                json={"token": token, "scanId": scan_id},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error updating scan status: {e}") from e

        result = HypergryphResponse[None].model_validate_json(response.content)

        if not result.is_success():
            raise AuthenticationError(result.msg, code=result.status)

        return True

    async def generate_scan_login(self) -> GenerateScanLoginData:
        """生成扫码登录的 scanId"""
        try:
            response = await self._http.post(
                "https://as.hypergryph.com/general/v1/gen_scan/login",
                headers=self._headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error generating scan login: {e}") from e

        result = HypergryphResponse[GenerateScanLoginData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def check_scan_login_status(
        self, scan_id: str
    ) -> CheckScanLoginStatusSuccessData | str:
        """检查扫码登录状态"""
        try:
            response = await self._http.get(
                "https://as.hypergryph.com/general/v1/scan_status",
                headers=self._headers,
                params={"scanId": scan_id},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error checking scan login status: {e}") from e

        result = HypergryphResponse[CheckScanLoginStatusSuccessData | None].model_validate_json(
            response.content
        )

        if result.data is not None:
            return result.data

        return result.msg

    async def token_by_scan_code(
        self, appCode: OAuth2AppCode, from_: int, scan_code: str
    ) -> HypergryphTokenData:
        """通过扫码返回的 scanCode 获取 token"""
        try:
            response = await self._http.post(
                "https://as.hypergryph.com/user/auth/v1/token_by_scan_code",
                headers=self._headers,
                json={"appCode": appCode.value, "from": from_, "scanCode": scan_code},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting token by scan code: {e}") from e

        result = HypergryphResponse[HypergryphTokenData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    async def get_u8_token_by_uid(self, uid: str, token: str) -> U8TokenByUidData:
        try:
            response = await self._http.post(
                "https://binding-api-account-prod.hypergryph.com/account/binding/v1/u8_token_by_uid",
                headers=self._headers,
                json={
                    "uid": uid,
                    "token": token,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting U8 token by UID: {e}") from e

        result = BindingAPIResponse[U8TokenByUidData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data

    # https://binding-api-account-prod.hypergryph.com/account/binding/v1/binding_list?appCode=endfield&token=token
    async def get_binding_list(self, app_code: OAuth2AppCode, token: str) -> BindingListData:
        """获取绑定列表"""
        try:
            response = await self._http.get(
                "https://binding-api-account-prod.hypergryph.com/account/binding/v1/binding_list",
                headers=self._headers,
                params={
                    "appCode": app_code.value,
                    "token": token,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting binding list: {e}") from e

        result = BindingAPIResponse[BindingListData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise AuthenticationError(result.msg, code=result.status)

        return result.data
