from typing import Type

from ....models.bots import DiscordCogBase
from .achievements import Achievements
from .general import General
from .setup import Setup


def all_cogs() -> list[Type[DiscordCogBase]]:
    return [Achievements, General, Setup]
