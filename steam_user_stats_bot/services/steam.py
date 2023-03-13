import asyncio
from typing import Any, Coroutine, TypeVar

from cachetools.func import ttl_cache

from ..clients.steam import SteamWebAPI
from ..config import STEAM_CACHE_TTL, STEAM_DEFAULT_REQUEST_TIMEOUT
from ..models.db import User
from ..models.exceptions import InvalidResponseException, InvalidSteamKeyException
from ..models.steam import (
    SteamGlobalGameStats,
    SteamUser,
    SteamUserGame,
    SteamUserGameStats,
)

T = TypeVar("T")


class SteamUserService:
    """Docs: https://developer.valvesoftware.com/wiki/Steam_Web_API"""

    def __init__(
        self, api_key: str, request_timeout: float | None = None, max_concurrency: int = 10, language: str = "en-US"
    ) -> None:
        self.api_key = api_key
        self.timeout = request_timeout or STEAM_DEFAULT_REQUEST_TIMEOUT
        self.max_concurrency = max_concurrency
        self.language = language

    def client(self):
        return SteamWebAPI(self.api_key, timeout=self.timeout)

    @classmethod
    def sync(cls, coroutine: Coroutine[Any, Any, T]) -> T:
        """Helper method to run a single async method"""
        return asyncio.run(coroutine)

    ### Users ###

    @classmethod
    async def check_if_user_is_valid(cls, user: User) -> bool:
        if not (user.steam_id_64 and user.steam_api_key):
            return False

        steam = SteamUserService(user.steam_api_key)
        try:
            user_summary = await steam.get_user_summary(user.steam_id_64)
            return bool(user_summary)

        except InvalidSteamKeyException:
            return False

    async def get_user_id_from_vanity_id(self, vanity_id: str) -> str | None:
        """
        Looks up a user's id using their vanity URL id

        i.e. https://steamcommunity.com/id/{vanity_id}
        """

        # remove URL if provided
        if "/" in vanity_id:
            vanity_id = vanity_id.rsplit("/", 1)[-1]

        async with self.client() as client, asyncio.Semaphore(self.max_concurrency):
            r = await client.get(client.url("/ISteamUser/ResolveVanityURL/v0001"), params={"vanityurl": vanity_id})
            response = r.json()

        return response["response"].get("steamid")

    async def get_user_summaries(self, user_ids: list[str]) -> list[SteamUser]:
        async with self.client() as client, asyncio.Semaphore(self.max_concurrency):
            r = await client.get(client.url("/ISteamUser/GetPlayerSummaries/v0002"), params={"steamids": user_ids})
            users = r.json()["response"]["players"]

        return [SteamUser.parse_obj(user) for user in users]

    @ttl_cache(ttl=STEAM_CACHE_TTL)
    async def get_user_summary(self, user_id: str) -> SteamUser | None:
        users = await self.get_user_summaries([user_id])
        return users[0] if users else None

    async def get_owned_games(
        self,
        user_id: str,
        include_played_free_games: bool = True,
        include_game_info: bool = False,
    ) -> list[SteamUserGame]:
        """
        Get a list of games owned by a user

        Args:
            user_id (str): The id of the steam user
            include_played_free_games (bool): Include free games that a user has played
            include_game_info (bool): Include additional game info
        """

        params: dict = {
            "steamid": user_id,
            "include_played_free_games": str(include_played_free_games).lower(),
            "include_appinfo": str(include_game_info).lower(),
        }

        async with self.client() as client, asyncio.Semaphore(self.max_concurrency):
            r = await client.get(client.url("/IPlayerService/GetOwnedGames/v0001"), params=params)
            games = r.json()["response"]["games"]

        return [SteamUserGame(**{"user_id": user_id} | game) for game in games]

    ### Achievements ###

    @ttl_cache(ttl=STEAM_CACHE_TTL)
    async def _get_global_achievement_stats_for_one_game(
        self, client: SteamWebAPI, game_id: str
    ) -> SteamGlobalGameStats:
        r = await client.get(
            client.url("/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002"), params={"gameid": game_id}
        )
        stats = r.json()["achievementpercentages"]
        return SteamGlobalGameStats(**{"app_id": game_id} | stats)

    async def get_global_achievement_stats(self, game_ids: list[str]) -> list[SteamGlobalGameStats]:
        async with self.client() as client, asyncio.Semaphore(self.max_concurrency):
            responses = await asyncio.gather(
                *[self._get_global_achievement_stats_for_one_game(client, game_id) for game_id in game_ids]
            )

        return responses

    @ttl_cache(ttl=STEAM_CACHE_TTL)
    async def _get_user_achievements_for_one_game(
        self, client: SteamWebAPI, user_id: str, game_id: str, include_global_percentages: bool = False
    ) -> SteamUserGameStats | None:
        try:
            r = await client.get(
                client.url("/ISteamUserStats/GetPlayerAchievements/v0001"),
                params={"steamid": user_id, "appid": game_id, "l": self.language},
            )
            stats = r.json()["playerstats"]
            if "error" in stats:
                return None

        except InvalidResponseException:
            return None

        user_stats = SteamUserGameStats(**{"app_id": game_id} | stats)
        if not include_global_percentages:
            return user_stats

        # fetch global stats and add to user stats
        global_stats = await self._get_global_achievement_stats_for_one_game(client, game_id)
        global_stats_by_achievement_name = {
            achievement.api_name: achievement for achievement in global_stats.achievements
        }
        for achievement in user_stats.achievements:
            if achievement.api_name in global_stats_by_achievement_name:
                achievement.global_percent = global_stats_by_achievement_name[achievement.api_name].percent

        return user_stats

    async def get_user_achievements(
        self, user_id: str, game_ids: list[str], include_global_percentages: bool = False
    ) -> list[SteamUserGameStats]:
        async with self.client() as client, asyncio.Semaphore(self.max_concurrency):
            responses = await asyncio.gather(
                *[
                    self._get_user_achievements_for_one_game(client, user_id, app_id, include_global_percentages)
                    for app_id in game_ids
                ]
            )

        return [r for r in responses if r]
