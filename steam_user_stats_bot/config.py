DB_DIR = "data/statsbot.db"
DB_URL = f"sqlite+pysqlite:///{DB_DIR}"

STEAM_WEB_API_BASE_URL = "http://api.steampowered.com"
STEAM_CACHE_TTL = 60 * 30
"""Cache TTL in seconds"""

DISCORD_BOT_PREFIX = "$"
DISCORD_ACHIEVEMENT_PAGE_SIZE = 6
DISCORD_PAGINATOR_TIMEOUT = 60
"""Timeout in seconds"""
