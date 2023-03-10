import asyncio

import discord
from discord.ext.commands import Bot

from ...config import DISCORD_BOT_PREFIX
from ...models.bots import DiscordCogBase
from .cogs import all_cogs

intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix=DISCORD_BOT_PREFIX, intents=intents)


def init_bot(token: str, **kwargs):
    async def _register(cogs: list[DiscordCogBase]):
        await asyncio.gather(*[bot.add_cog(cog) for cog in cogs])

    cogs: list[DiscordCogBase] = [cog(bot) for cog in all_cogs()]
    asyncio.run(_register(cogs))
    bot.run(token, **kwargs)
