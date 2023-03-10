import argparse

from steam_user_stats_bot.bots.discord.bot import init_bot
from steam_user_stats_bot.db.setup import init_db

parser = argparse.ArgumentParser(prog="Steam User Stats Bot", description="Discord bot for steam user stats")
parser.add_argument("discord_key", type=str, help="your Discord Bot API Key")


def main() -> None:
    args = parser.parse_args()
    discord_key: str = args.discord_key

    init_db()
    init_bot(discord_key)


if __name__ == "__main__":
    main()
