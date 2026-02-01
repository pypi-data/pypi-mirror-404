from enum import IntEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PlatformEnum(IntEnum):
    ANDROID = 0
    IOS = 1
    WINDOWS = 2


class HypergryphDeviceWindows(BaseModel):
    type: Literal["windows"]
    device_id: str
    device_id2: str
    device_model: str
    device_type: PlatformEnum = PlatformEnum.WINDOWS


class HypergryphDeviceAndroid(BaseModel):
    type: Literal["android"]
    did: str


HypergryphDevice = Annotated[
    HypergryphDeviceWindows | HypergryphDeviceAndroid, Field(discriminator="type")
]
