from discord.ext import commands
from discord.ext.commands import Context, MissingRequiredArgument, command
from discord.ext.commands.errors import CommandInvokeError

from ....config import DISCORD_BOT_PREFIX
from ....models.bots import DiscordCogBase
from ....models.db import User
from ....models.exceptions import InvalidResponseException, InvalidSteamKeyException
from ....services.steam import SteamUserService
from .. import db


class Setup(DiscordCogBase):
    @command(brief="Set up access using your Steam API key, and your steamID64 or vanityID")
    async def setup(
        self,
        ctx: Context,
        steam_api_key: str = commands.parameter(
            description="Your Steam API key: https://steamcommunity.com/dev/apikey"
        ),
        steam_user_id: str = commands.parameter(description="Your steamID64 or vanityID: https://steamidfinder.com"),
    ):
        f"""
        Set up access using your Steam API key, and your steamID64 or vanityID.

        Ex: `{DISCORD_BOT_PREFIX}setup E45MLZDJ3DF13R416Y4KYJ67K1UCM93J 73244020282149373`
        or: `{DISCORD_BOT_PREFIX}setup E45MLZDJ3DF13R416Y4KYJ67K1UCM93J your-profile-name`
        """

        steam = SteamUserService(steam_api_key)
        if not steam_user_id.isnumeric():
            steam_user_id = await steam.get_user_id_from_vanity_id(steam_user_id) or ""
            if not steam_user_id:
                raise InvalidResponseException()

        user = User(id=str(ctx.author.id), steam_id_64=steam_user_id, steam_api_key=steam_api_key)
        if not await steam.check_if_user_is_valid(user):
            raise InvalidResponseException()

        existing_user = db.get_user(user.id)
        if existing_user:
            db.update_user(user)

        else:
            db.create_user(user)

        # TODO: add "Try running XXX"
        await ctx.send("Thanks, you're all set!")

    @setup.error
    async def setup_error(self, ctx: Context, ex: Exception):
        if isinstance(ex, MissingRequiredArgument):
            await ctx.send(
                "Missing one or more arguments. Make sure you supply your Steam API key, then your steamID64 or vanityID, seperated by a space\n"
                + f"Ex: `{DISCORD_BOT_PREFIX}setup E45MLZDJ3DF13R416Y4KYJ67K1UCM93J 73244020282149373`"
            )
            await ctx.send(
                "Alternatively, you may supply your unique vanityID instead of your steamID64, which is usually the username you use to log in\n"
                + "Ex: `https://steamcommunity.com/id/{vanityID}`"
            )

        elif isinstance(ex, CommandInvokeError):
            ex = ex.original
            if isinstance(ex, InvalidSteamKeyException):
                await ctx.send("Invalid Steam API key. Please verify that you copied it correctly")

            elif isinstance(ex, InvalidResponseException):
                await ctx.send(
                    "Invalid Invalid Steam API key, or steamID64/vanityID. Make sure you supply your Steam API key, then your steamID64 or vanityID, seperated by a space\n"
                    + f"Ex: `{DISCORD_BOT_PREFIX}setup E45MLZDJ3DF13R416Y4KYJ67K1UCM93J 73244020282149373`"
                )

            else:
                print(f"{type(ex).__name__}: {ex}")  # TODO: have better exception logging
                await ctx.send("Oops, something went wrong!")
                return

        await ctx.send(
            "Find your API key here: https://steamcommunity.com/dev/apikey\n"
            + "Find your steamID64 here: https://steamidfinder.com",
            suppress_embeds=True,
        )
