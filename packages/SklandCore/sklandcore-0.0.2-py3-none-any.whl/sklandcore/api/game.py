from typing import Literal

import httpx

from ..constants import (
    SKLAND_ATTENDANCE_URL,
    SKLAND_HEADERS,
    SKLAND_PLAYER_BINDING_URL,
    SKLAND_PLAYER_INFO_URL,
)
from ..exceptions import (
    AlreadySignedError,
    GameNotBoundError,
    NetworkError,
    PlayerNotFoundError,
    RequestError,
)
from ..models.base import SklandResponse
from ..models.game import AttendanceData, BindingData, GameBinding, PlayerData
from ..signature import get_signed_headers


class GameAPI:
    def __init__(
        self,
        cred: str,
        token: str,
        http_client: httpx.AsyncClient,
        device_id: str,
    ):
        self.cred = cred
        self.token = token
        self._http = http_client
        self._device_id = device_id

    def _get_headers(
        self,
        url: str,
        method: Literal["GET", "POST"],
        body: dict | None = None,
    ) -> dict[str, str]:
        return get_signed_headers(
            url=url,
            method=method,
            body=body,
            base_headers=SKLAND_HEADERS,
            sign_token=self.token,
            cred=self.cred,
            device_id=self._device_id,
        )

    async def get_binding_list(self) -> list[GameBinding]:
        headers = self._get_headers(SKLAND_PLAYER_BINDING_URL, "GET")

        try:
            response = await self._http.get(
                SKLAND_PLAYER_BINDING_URL,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting bindings: {e}") from e

        result = SklandResponse[BindingData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            raise RequestError(result.message, code=result.code)

        return result.data.list

    async def get_player_info(self, uid: str) -> PlayerData:
        url = f"{SKLAND_PLAYER_INFO_URL}?uid={uid}"
        headers = self._get_headers(url, "GET")

        try:
            response = await self._http.get(
                url,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error getting player info: {e}") from e

        result = SklandResponse[PlayerData].model_validate_json(response.content)

        if not result.is_success() or result.data is None:
            if "玩家不存在" in result.message:
                raise PlayerNotFoundError(result.message, code=result.code)
            raise RequestError(result.message, code=result.code)

        return result.data

    async def attendance(self, uid: str, game_id: str) -> AttendanceData:
        body = {"uid": uid, "gameId": game_id}
        headers = self._get_headers(SKLAND_ATTENDANCE_URL, "POST", body)

        try:
            response = await self._http.post(
                SKLAND_ATTENDANCE_URL,
                headers=headers,
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error during attendance: {e}") from e

        result = SklandResponse[AttendanceData].model_validate_json(response.content)

        if not result.is_success():
            if "请勿重复签到" in result.message:
                raise AlreadySignedError(result.message, code=result.code)
            if "绑定" in result.message or "角色" in result.message:
                raise GameNotBoundError(result.message, code=result.code)
            raise RequestError(result.message, code=result.code, data=result.data)

        if result.data is None:
            raise RequestError("Empty response data", code=result.code)

        return result.data

    async def get_arknights_binding(self) -> GameBinding | None:
        bindings = await self.get_binding_list()
        for binding in bindings:
            if binding.appCode == "arknights":
                return binding
        return None

    async def attendance_arknights(self, uid: str) -> AttendanceData:
        binding = await self.get_arknights_binding()
        if binding is None:
            raise GameNotBoundError("Arknights is not bound to this account")

        # Find the correct channelMasterId for this UID
        game_id = "1"  # Default to official server
        for role in binding.bindingList:
            if role.uid == uid:
                game_id = role.channelMasterId
                break

        return await self.attendance(uid, game_id)

    async def get_beyond_binding(self) -> GameBinding | None:
        bindings = await self.get_binding_list()
        for binding in bindings:
            if binding.appCode == "endfield":
                return binding
        return None

    async def attendance_beyond(self, uid: str) -> AttendanceData:
        binding = await self.get_beyond_binding()
        if binding is None:
            raise GameNotBoundError("Beyond is not bound to this account")

        # Find the correct channelMasterId for this UID
        game_id = "1"  # Default to official server
        for role in binding.bindingList:
            if role.uid == uid:
                game_id = role.channelMasterId
                break

        return await self.attendance(uid, game_id)
