from http import HTTPStatus
from typing import Any, Callable

from httpx import AsyncClient, HTTPStatusError, Response

from ..config import STEAM_WEB_API_BASE_URL
from ..models.exceptions import InvalidResponseException, InvalidSteamKeyException


class SteamWebAPI(AsyncClient):
    def __init__(self, api_key: str, format: str = "json", timeout: float = 5, **kwargs):
        kwargs = self._inject_params(api_key, format, timeout, **kwargs)
        kwargs = self._inject_hooks(**kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _inject_params(cls, api_key: str, format: str, timeout: float, **kwargs):
        """Inject steam-specific params"""

        if "params" in kwargs:
            params: dict = kwargs["params"]
        else:
            params = {}

        # inject steam params
        params["key"] = api_key
        params["format"] = format

        kwargs["params"] = params
        kwargs["timeout"] = timeout
        return kwargs

    @classmethod
    def _inject_hooks(cls, **kwargs) -> dict[str, Any]:
        if "event_hooks" in kwargs:
            event_hooks: dict[str, list[Callable]] = kwargs["event_hooks"]
        else:
            event_hooks = {}

        event_hooks.setdefault("request", []).extend([])
        event_hooks.setdefault("response", []).extend([cls.check_steam_response])

        kwargs["event_hooks"] = event_hooks
        return kwargs

    @classmethod
    def url(cls, endpoint) -> str:
        if not endpoint:
            return STEAM_WEB_API_BASE_URL

        if endpoint[0] == "/":
            endpoint = endpoint[1:]

        return f"{STEAM_WEB_API_BASE_URL}/{endpoint}"

    @classmethod
    async def check_steam_response(cls, response: Response) -> None:
        """Raises an exception if the response is invalid"""

        if response.status_code == HTTPStatus.FORBIDDEN.value:
            await response.aread()
            raise InvalidSteamKeyException(response.content.decode())

        try:
            response.raise_for_status()
        except HTTPStatusError as e:
            await response.aread()
            raise InvalidResponseException(detail=e.response.content.decode()) from e
