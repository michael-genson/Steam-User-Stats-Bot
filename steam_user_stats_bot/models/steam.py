from datetime import datetime
from enum import Enum

from pydantic import Field, root_validator, validator

from ._base import StatsBotBaseModel

### Users ###


class SteamUserAvatar(StatsBotBaseModel):
    small_url: str = Field(alias="avatar")
    medium_url: str = Field(alias="avatarmedium")
    large_url: str = Field(alias="avatarfull")


class SteamUserStatus(Enum):
    offline = 0
    online = 1
    busy = 2
    away = 3
    snooze = 4
    looking_to_trade = 5
    looking_to_play = 6


class SteamUser(StatsBotBaseModel):
    steam_id: str = Field(alias="steamid")
    display_name: str = Field(alias="personaname")
    profile_url: str = Field(alias="profileurl")
    avatar: SteamUserAvatar
    status: SteamUserStatus = Field(alias="personastate")
    is_visible: bool = Field(alias="communityvisibilitystate")
    profile_is_configured: bool = Field(alias="profilestate")
    last_online: datetime | None = Field(None, alias="lastlogoff")
    allows_comments: bool = Field(alias="commentpermission")

    @root_validator(pre=True)
    def build_subclasses(cls, values: dict):
        values["avatar"] = SteamUserAvatar(**values)
        return values

    @validator("is_visible", pre=True)
    def profile_is_visible(cls, v) -> bool:
        return v == 3 or v == "3"

    @validator("last_online", pre=True)
    def parse_unix_time(cls, v) -> datetime | None:
        return datetime.fromtimestamp(v) if v else None


class SteamUserGamePlaytime(StatsBotBaseModel):
    all_time: int = Field(alias="playtime_forever")
    """A User's total playtime, in minutes"""

    all_time_windows: int = Field(alias="playtime_windows_forever")
    """A User's total playtime on a Windows platform, in minutes"""

    all_time_mac: int = Field(alias="playtime_mac_forever")
    """A User's total playtime on a Mac platform, in minutes"""

    all_time_linux: int = Field(alias="playtime_linux_forever")
    """A User's total playtime on a Linux platform, in minutes"""


class SteamUserGame(StatsBotBaseModel):
    app_id: str = Field(alias="appid")
    user_id: str
    playtime: SteamUserGamePlaytime
    last_played: datetime | None = Field(None, alias="rtime_last_played")

    # only populated if include_game_info is set in request
    name: str | None = None
    icon_url: str | None = Field(None, alias="img_icon_url")
    logo_url: str | None = Field(None, alias="img_logo_url")
    user_has_public_stats: bool = Field(False, alias="has_community_visible_stats")

    @root_validator(pre=True)
    def build_subclasses(cls, values: dict):
        values["playtime"] = SteamUserGamePlaytime(**values)
        return values

    @validator("last_played", pre=True)
    def parse_unix_time(cls, v) -> datetime | None:
        return datetime.fromtimestamp(v) if v else None

    @validator("icon_url", "logo_url")
    def build_image_url(cls, v, values):
        return f"http://media.steampowered.com/steamcommunity/public/images/apps/{values['app_id']}/{v}.jpg"


### Achievements ###
class SteamGlobalGameStatsAchievement(StatsBotBaseModel):
    api_name: str = Field(alias="name")
    percent: float


class SteamGlobalGameStats(StatsBotBaseModel):
    app_id: str
    achievements: list[SteamGlobalGameStatsAchievement]

    @root_validator(pre=True)
    def build_achievements(cls, values: dict):
        values["achievements"] = [
            SteamGlobalGameStatsAchievement(**achievement) for achievement in values.pop("achievements", [])
        ]
        return values


class SteamUserGameStatsAchievement(StatsBotBaseModel):
    game_name: str
    api_name: str = Field(alias="apiname")
    display_name: str | None = Field(None, alias="name")
    description: str | None = None

    achieved: bool
    achieved_at: datetime | None = Field(None, alias="unlocktime")
    global_percent: float | None = None

    @validator("achieved_at", pre=True)
    def parse_unix_time(cls, v) -> datetime | None:
        return datetime.fromtimestamp(v) if v else None


class SteamUserGameStats(StatsBotBaseModel):
    app_id: str
    user_id: str = Field(alias="steamID")

    name: str = Field(alias="gameName")
    achievements: list[SteamUserGameStatsAchievement]

    @root_validator(pre=True)
    def build_achievements(cls, values: dict):
        values["achievements"] = [
            SteamUserGameStatsAchievement(**{"game_name": values["gameName"]} | achievement)
            for achievement in values.pop("achievements", [])
        ]
        return values
