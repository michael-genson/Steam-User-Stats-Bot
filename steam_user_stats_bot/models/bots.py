from discord.ext.commands import Cog


class DiscordCogBase(Cog):
    def __init__(self, bot):
        self.bot = bot
