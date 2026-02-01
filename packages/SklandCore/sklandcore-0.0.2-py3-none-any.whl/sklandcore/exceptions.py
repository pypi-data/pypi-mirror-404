"""Exceptions for Skland API."""

from typing import Any


class SklandError(Exception):
    """Base exception for all Skland API errors."""

    def __init__(self, message: str, code: int | None = None, data: Any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)

    def __str__(self) -> str:
        if self.code is not None:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(SklandError):
    """Raised when authentication fails."""

    pass


class InvalidCredentialError(AuthenticationError):
    """Raised when the credential is invalid or expired."""

    pass


class LoginError(AuthenticationError):
    """Raised when login fails."""

    pass


class RequestError(SklandError):
    """Raised when an API request fails."""

    pass


class NetworkError(RequestError):
    """Raised when a network error occurs."""

    pass


class RateLimitError(RequestError):
    """Raised when rate limit is exceeded."""

    pass


class ServerError(RequestError):
    """Raised when the server returns an error."""

    pass


class PlayerNotFoundError(SklandError):
    """Raised when a player is not found."""

    pass


class GameNotBoundError(SklandError):
    """Raised when the game is not bound to the account."""

    pass


class AlreadySignedError(SklandError):
    """Raised when the user has already signed in today."""

    pass


class SignatureError(SklandError):
    """Raised when signature generation or verification fails."""

    pass
