import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from loguru import logger

from .api.game import GameAPI
from .auth.hypergryph import HypergryphAuth
from .auth.skland import SklandAuth
from .constants import (
    SKLAND_HEADERS,
    TOKEN_REFRESH_MAX_RETRIES,
    TOKEN_REFRESH_RETRY_DELAY,
    OAuth2AppCode,
)
from .did_manager import get_or_create_did
from .exceptions import AuthenticationError, InvalidCredentialError
from .models.auth import GrantCodeDataType0, HypergryphTokenData, SKlandCredential, UserCheckData
from .models.game import AttendanceData, GameBinding, PlayerData

T = TypeVar("T")


class SklandClient:
    def __init__(self, phone: str):
        self._phone = phone

        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._device_id = await get_or_create_did(self._phone)
        logger.info(f"Device ID: {self._device_id}")

        self._http = httpx.AsyncClient(timeout=30.0)
        self._hypergryph_auth = HypergryphAuth(http_client=self._http, headers=SKLAND_HEADERS)
        self._skland_auth = SklandAuth(http_client=self._http, device_id=self._device_id)
        self._game_api = None

    async def initialize_from_cred(self, cred: str, token: str) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._cred = cred
        self._token = token
        self._device_id = await get_or_create_did(cred)

        self._http = httpx.AsyncClient(timeout=30.0)
        self._hypergryph_auth = HypergryphAuth(http_client=self._http, headers=SKLAND_HEADERS)
        self._skland_auth = SklandAuth(http_client=self._http, device_id=self._device_id)
        self._game_api = None

    @property
    def cred(self) -> str | None:
        return self._cred

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def device_id(self) -> str | None:
        return self._device_id

    @property
    def is_authenticated(self) -> bool:
        return self._cred is not None and self._token is not None

    async def _ensure_device_id(self) -> str:
        if self._device_id is None:
            if self._cred is None:
                raise AuthenticationError("Credential is not set. Please login first.")
            self._device_id = await get_or_create_did(self._cred)
        return self._device_id

    async def _get_game_api(self) -> GameAPI:
        if self._game_api is None:
            if not self.is_authenticated:
                raise AuthenticationError("Not authenticated. Please login first.")
            if self._cred is None or self._token is None:
                raise AuthenticationError("Credential or token is not set. Please login first.")
            device_id = await self._ensure_device_id()
            self._game_api = GameAPI(
                cred=self._cred,
                token=self._token,
                http_client=self._http,
                device_id=device_id,
            )
        return self._game_api

    def _reset_game_api(self) -> None:
        self._game_api = None

    async def _try_refresh_token(
        self,
        max_retries: int = TOKEN_REFRESH_MAX_RETRIES,
        retry_delay: float = TOKEN_REFRESH_RETRY_DELAY,
    ) -> bool:
        if self._cred is None or self._token is None:
            return False

        for attempt in range(TOKEN_REFRESH_MAX_RETRIES):
            try:
                new_token = await self._skland_auth.refresh_token(
                    cred=self._cred,
                    old_token=self._token,
                    max_retries=1,
                    retry_delay=0,
                )
                self._token = new_token
                self._reset_game_api()
                return True
            except InvalidCredentialError:
                # Token expired, cannot refresh with same credentials
                return False
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        return False

    async def _execute_with_auto_refresh(self, operation: Callable[[], Awaitable[T]]) -> T:
        try:
            return await operation()
        except InvalidCredentialError:
            if await self._try_refresh_token():
                return await operation()
            raise

    async def refresh_token(self) -> str:
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated")
        if self._cred is None or self._token is None:
            raise AuthenticationError("Credential or token is not set. Please login first.")

        new_token = await self._skland_auth.refresh_token(cred=self._cred, old_token=self._token)
        self._token = new_token
        self._reset_game_api()
        return new_token

    async def login_by_password(
        self, app_code: OAuth2AppCode, password: str, device_token: str
    ) -> SKlandCredential:
        # Step 1: Get account token
        account_token = await self._hypergryph_auth.login_by_password(self._phone, password)

        # Step 2: Get grant code
        grant_data = await self._hypergryph_auth.get_grant_code(
            app_code, account_token.token, device_token, 0
        )

        assert isinstance(grant_data, GrantCodeDataType0)

        # Step 3: Generate credential
        credential = await self._skland_auth.generate_cred_by_code(grant_data.code)

        # Update client state
        self._cred = credential.cred
        self._token = credential.token
        self._reset_game_api()

        return credential

    async def send_phone_code(self) -> bool:
        return await self._hypergryph_auth.send_phone_code(self._phone)

    async def login_by_code(self, app_code: OAuth2AppCode, code: str) -> SKlandCredential:
        # Step 1: Get account token
        account_token = await self._hypergryph_auth.login_by_code(app_code, self._phone, code)

        # Step 2: Get grant code
        grant_data = await self._hypergryph_auth.get_grant_code(
            app_code, account_token.token, account_token.deviceToken, 0
        )

        assert isinstance(grant_data, GrantCodeDataType0)

        # Step 3: Generate credential
        credential = await self._skland_auth.generate_cred_by_code(grant_data.code)

        # Update client state
        self._cred = credential.cred
        self._token = credential.token
        self._reset_game_api()

        return credential

    async def login_by_token(
        self, app_code: OAuth2AppCode, account_token: HypergryphTokenData
    ) -> SKlandCredential:
        # Get grant code
        grant_data = await self._hypergryph_auth.get_grant_code(
            app_code, account_token.token, account_token.deviceToken, 0
        )
        assert isinstance(grant_data, GrantCodeDataType0)

        # Generate credential
        credential = await self._skland_auth.generate_cred_by_code(grant_data.code)

        # Update client state
        self._cred = credential.cred
        self._token = credential.token
        self._reset_game_api()

        return credential

    def set_credential(self, cred: str, token: str) -> None:
        self._cred = cred
        self._token = token
        self._reset_game_api()

    async def check_credential(self) -> UserCheckData:
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated")
        if self._cred is None or self._token is None:
            raise AuthenticationError("Credential or token is not set. Please login first.")

        async def _check_credential() -> UserCheckData:
            if self._cred is None or self._token is None:
                raise AuthenticationError("Credential or token is not set.")
            return await self._skland_auth.check_cred(self._cred, self._token)

        return await self._execute_with_auto_refresh(_check_credential)

    async def get_binding_list(self) -> list[GameBinding]:
        async def _get_binding_list() -> list[GameBinding]:
            game_api = await self._get_game_api()
            return await game_api.get_binding_list()

        return await self._execute_with_auto_refresh(_get_binding_list)

    async def get_player_info(self, uid: str) -> PlayerData:
        async def _get_player_info() -> PlayerData:
            game_api = await self._get_game_api()
            return await game_api.get_player_info(uid)

        return await self._execute_with_auto_refresh(_get_player_info)

    async def attendance(self, uid: str, game_id: str) -> AttendanceData:
        async def _attendance() -> AttendanceData:
            game_api = await self._get_game_api()
            return await game_api.attendance(uid, game_id)

        return await self._execute_with_auto_refresh(_attendance)

    async def get_arknights_binding(self) -> GameBinding | None:
        async def _get_arknights_binding() -> GameBinding | None:
            game_api = await self._get_game_api()
            return await game_api.get_arknights_binding()

        return await self._execute_with_auto_refresh(_get_arknights_binding)

    async def attendance_arknights(self, uid: str) -> AttendanceData:
        async def _attendance_arknights() -> AttendanceData:
            game_api = await self._get_game_api()
            return await game_api.attendance_arknights(uid)

        return await self._execute_with_auto_refresh(_attendance_arknights)

    async def get_beyond_binding(self) -> GameBinding | None:
        async def _get_beyond_binding() -> GameBinding | None:
            game_api = await self._get_game_api()
            return await game_api.get_beyond_binding()

        return await self._execute_with_auto_refresh(_get_beyond_binding)

    async def attendance_beyond(self, uid: str) -> AttendanceData:
        async def _attendance_beyond() -> AttendanceData:
            game_api = await self._get_game_api()
            return await game_api.attendance_beyond(uid)

        return await self._execute_with_auto_refresh(_attendance_beyond)
