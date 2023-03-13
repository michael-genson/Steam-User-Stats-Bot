from discord.ext import commands
from discord.ext.commands import Context

from ...config import DISCORD_BOT_PREFIX
from ...models.exceptions import UserNotSetupException
from ...services.db import UserDBService

db = UserDBService()


def require_setup_user():
    async def wrapper(ctx: Context) -> bool:
        user = db.get_user(ctx.author.id)
        if not (user and user.is_setup):
            await ctx.send(f"You are not set up! Try running `{DISCORD_BOT_PREFIX}setup` first")
            raise UserNotSetupException(ctx.author.name)

        return True

    return commands.check(wrapper)
