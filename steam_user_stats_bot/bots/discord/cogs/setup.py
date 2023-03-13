from discord.ext import commands
from discord.ext.commands import Context, MissingRequiredArgument, command
from discord.ext.commands.errors import CommandInvokeError

from ....config import DISCORD_BOT_PREFIX
from ....models.bots import DiscordCogBase
from ....models.db import User
from ....models.exceptions import (
    InvalidResponseException,
    InvalidSteamKeyException,
    UserNotSetupException,
)
from ....services.steam import SteamUserService
from .. import db, require_setup_user


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

    @command()
    async def get_steam_info(self, ctx: Context):
        """Check out your stored Steam user info, if you're set up"""

        user = db.get_user(ctx.author.id)
        if not user:
            await ctx.send("No steam user info found")
            return

        await ctx.send(f"API Key: {user.steam_api_key or 'UNKNOWN'}\nsteamID64: {user.steam_id_64 or 'UNKNOWN'}")

    @command()
    @require_setup_user()
    async def get_profile_url(self, ctx: Context):
        """Look up your on Steam profile URL"""

        user = db.get_user(ctx.author.id)
        if not (user and user.steam_api_key and user.steam_id_64):
            return

        steam = SteamUserService(user.steam_api_key)
        steam_user = await steam.get_user_summary(user.steam_id_64)
        if not steam_user:
            await ctx.send(f"User not found. Try running `{DISCORD_BOT_PREFIX}setup` again")
            return

        await ctx.send(f"Your profile URL is {steam_user.profile_url}")
        return

    @get_profile_url.error
    async def achievement_error(self, ctx: Context, ex: Exception):
        if isinstance(ex, UserNotSetupException):
            # require_setup_user already handles this
            return

        print(f"{type(ex).__name__}: {ex}")  # TODO: have better exception logging
        await ctx.send("Oops, something went wrong!")
        return
