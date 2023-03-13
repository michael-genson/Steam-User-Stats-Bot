import Paginator  # type: ignore
from discord import Embed
from discord.ext.commands import Context, command

from ....config import DISCORD_ACHIEVEMENT_PAGE_SIZE, DISCORD_PAGINATOR_TIMEOUT
from ....models.bots import DiscordCogBase
from ....models.steam import SteamUserGameStatsAchievement
from ....services.steam import SteamUserService
from .. import db, require_setup_user
from ..utils import chunk_list


class Achievements(DiscordCogBase):
    @classmethod
    def format_achievement(cls, achievement: SteamUserGameStatsAchievement, include_game: bool = True) -> str:
        builder: list[str] = []

        # HALF-LIFE 2
        # -----
        if include_game:
            builder.append(f"[{achievement.game_name.upper()}]")
            builder.append("-----")

        # Lambda Locator
        # Find all lambda caches in Half-Life 2.
        builder.append(achievement.display_name or achievement.api_name)
        if achievement.description:
            builder.append(achievement.description)

        #
        # Achieved Nov 16, 2004
        builder.append("")
        if achievement.achieved:
            component = "Achieved"
            if achievement.achieved_at:
                component += f" {achievement.achieved_at.strftime('%b %d, %Y')}"

            builder.append(component)
        else:
            builder.append("Not Achieved")

        # 3.33% of players have this achievement
        if achievement.global_percent is not None:
            builder.append(f"{achievement.global_percent:.1f}% of players have this achievement")

        nl = "\n"
        return f"```{nl.join(builder)}```"

    @command()
    @require_setup_user()
    async def check_rare_achievements(self, ctx: Context):
        """Show your rarest achievements"""

        user = db.get_user(ctx.author.id)
        if not (user and user.steam_api_key and user.steam_id_64):
            return

        steam = SteamUserService(user.steam_api_key)
        all_owned_games = await steam.get_owned_games(user.steam_id_64)
        stats = await steam.get_user_achievements(
            user.steam_id_64,
            [game.app_id for game in all_owned_games],
            include_global_percentages=True,
        )

        achievements = [achievement for stat in stats for achievement in stat.achievements if achievement.achieved]
        achievements.sort(key=lambda x: x.global_percent or 0)

        embeds: list[Embed] = []
        for chunk in chunk_list(achievements, DISCORD_ACHIEVEMENT_PAGE_SIZE):
            embeds.append(
                Embed(
                    title=f"Your Achievements",
                    description="\n".join([self.format_achievement(achievement) for achievement in chunk]),
                )
            )

        await Paginator.Simple(timeout=DISCORD_PAGINATOR_TIMEOUT).start(ctx, pages=embeds)
