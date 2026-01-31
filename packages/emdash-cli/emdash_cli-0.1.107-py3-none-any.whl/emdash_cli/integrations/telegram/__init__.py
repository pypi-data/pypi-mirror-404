"""Telegram integration for EmDash CLI.

This module provides integration with Telegram Bot API to receive
and respond to messages via Telegram while running the local EmDash agent.
"""

from .config import TelegramConfig, get_config, save_config
from .bot import TelegramBot

__all__ = [
    "TelegramConfig",
    "TelegramBot",
    "get_config",
    "save_config",
]
