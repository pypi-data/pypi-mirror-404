from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HypergryphResponse(BaseModel, Generic[T]):
    status: int
    type: str
    msg: str
    data: T | None = None

    def is_success(self) -> bool:
        return self.status == 0


class SklandResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None = None

    def is_success(self) -> bool:
        return self.code == 0


class BindingAPIResponse(BaseModel, Generic[T]):
    status: int
    msg: str
    data: T | None = None

    def is_success(self) -> bool:
        return self.status == 0
