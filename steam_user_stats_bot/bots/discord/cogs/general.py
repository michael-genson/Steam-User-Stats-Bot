from discord.ext.commands import Context, command

from ....models.bots import DiscordCogBase


class General(DiscordCogBase):
    @command()
    async def ping(self, ctx: Context):
        await ctx.send("Pong!")
