from typing import TypeVar

from discord.ext.commands.errors import CommandError

T = TypeVar("T")


### DB ###


class NotFoundException(Exception):
    def __init__(self, db_model: T, detail: str | None = None):
        message = f"{db_model} not found"
        if detail:
            message += f" ({detail})"

        super().__init__(message)


class InvalidResponseException(Exception):
    """Generic invalid response"""

    def __init__(self, message: str | None = None, detail: str | None = None):
        message = message or "Invalid response"
        if detail:
            message += f" ({detail})"

        super().__init__(message)


### Steam ###


class InvalidSteamKeyException(InvalidResponseException):
    """Raised when a request is made to the Steam API with an invalid API key"""

    def __init__(self, detail: str | None = None):
        message = "Invalid steam key. Please verify your API key"
        super().__init__(message, detail)


### Discord ###


class UserNotSetupException(CommandError):
    def __init__(self, user: str):
        super().__init__(f"User {user} is not set up")
