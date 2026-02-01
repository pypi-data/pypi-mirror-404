from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class U8Response(BaseModel, Generic[T]):
    """Data from U8 response."""

    data: T | None = None
    msg: str
    status: int
    type: str

    def is_success(self) -> bool:
        return self.status == 0


class TokenByChannelTokenData(BaseModel):
    """Data from U8 token by channel token response."""

    token: str
    isNew: bool
    uid: str


class U8GrantCodeData(BaseModel):
    """Data from U8 grant code response."""

    uid: str
    code: str
    token: str
