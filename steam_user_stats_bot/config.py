import logging
import os
from typing import Callable, TypeVar

T = TypeVar("T")


def _load(env_var_name: str, default: T, func: Callable[[str], T]) -> T:
    """Load an environment variable or use the default"""

    if (val := os.environ.get(env_var_name)) is None:
        return default

    try:
        loaded_val = func(val)

        logging.info(f"Loaded {env_var_name} value '{loaded_val}' from environment")
        return loaded_val

    except Exception:
        logging.warn(f"Failed to load {env_var_name} value '{val}' from environment; using default of '{default}'")
        return default


DB_DIR = _load("DB_DIR", "data/statsbot.db", str)
DB_URL = f"sqlite+pysqlite:///{DB_DIR}"

STEAM_WEB_API_BASE_URL = "http://api.steampowered.com"
STEAM_CACHE_TTL = _load("STEAM_CACHE_TTL", 60 * 30, int)
"""Cache TTL in seconds"""

DISCORD_BOT_PREFIX = _load("DISCORD_BOT_PREFIX", "$", str)
DISCORD_ACHIEVEMENT_PAGE_SIZE = _load("DISCORD_ACHIEVEMENT_PAGE_SIZE", 6, int)
DISCORD_PAGINATOR_TIMEOUT = _load("DISCORD_PAGINATOR_TIMEOUT", 60, int)
"""Timeout in seconds"""
