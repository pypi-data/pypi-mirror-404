from pydantic import BaseModel


class HypergryphTokenData(BaseModel):
    """Data from Hypergryph token authentication response."""

    token: str
    hgId: str
    deviceToken: str


class TokenByPasswordData(BaseModel):
    """Data from Hypergryph token by password response."""

    token: str


class GrantCodeDataType0(BaseModel):
    """Data from OAuth2 grant code response."""

    code: str
    uid: str


class GrantCodeDataType1(BaseModel):
    """Data from OAuth2 grant code response (type 1)."""

    token: str
    uid: str


class GrantCodeDataType1BindingAPI(BaseModel):
    """Data from OAuth2 grant code response (type 1, Binding API)."""

    token: str
    hgId: str


class U8TokenByUidData(BaseModel):
    """Data from U8 token by UID response."""

    token: str


class BindingListRoleItem(BaseModel):
    """Role item in the binding list."""

    isBanned: bool
    serverId: str
    serverName: str
    roleId: str
    nickName: str
    level: int
    isDefault: bool
    registerTs: int


class BindingListItem(BaseModel):
    """Single item in the binding list."""

    uid: str
    isOfficial: bool
    isDefault: bool
    channelMasterId: int
    channelName: str
    isDeleted: bool
    isBanned: bool
    registerTs: int
    roles: list[BindingListRoleItem]


class BindingData(BaseModel):
    """Data from player binding response."""

    appCode: str
    appName: str
    supportMultiServer: bool
    bindingList: list[BindingListItem]


class BindingListData(BaseModel):
    """Data from Binding List response."""

    list: list[BindingData]


class SKlandCredential(BaseModel):
    """Skland credential data.

    Contains both 'cred' (for API authentication) and 'token' (for signing).
    """

    cred: str
    token: str
    userId: str


class BeyondCredential(BaseModel):
    """Beyond credential data."""

    code: str
    token: str
    grantToken: str
    userId: str


class UserBasicInfo(BaseModel):
    """User basic info from Hypergryph API."""

    hgId: str
    phone: str
    email: str | None
    identityNum: str
    identityName: str
    isMinor: bool
    isLatestUserAgreement: bool


class UserCheckData(BaseModel):
    """Data from Skland user check response."""

    policyList: list[str]
    isNewUser: bool


class TokenRefreshData(BaseModel):
    """Data from token refresh response."""

    token: str


class SklandUserInfo(BaseModel):
    """Skland user info."""

    id: str
    nickname: str
    avatar: str
    gender: int
    signature: str
    birthday: str
    backgroundHomeImage: str


class ScanLoginAppInfo(BaseModel):
    """Scan login application info."""

    name: str
    appCode: str
    iconUrl: str


class GenerateScanLoginData(BaseModel):
    """Data from generate scan login response."""

    scanId: str
    scanUrl: str
    enableScanAppList: list[ScanLoginAppInfo]


class CheckScanLoginStatusSuccessData(BaseModel):
    """Data from check scan login status response when successful."""

    scanCode: str
