"""
Telegram channel implementation.

Sends messages with inline "Mark Paid" buttons via the Bot API, and supports
polling for three kinds of inbound interaction:
  1. Button tap -> callback_data like "paid:<card_id>"
  2. Typed "/paid <card name>" command
  3. "/addcard" — a multi-step conversation that walks the user through
     adding a new card (name, last 4 digits, bill date, reminder window)
     without touching the command line. This is Telegram-specific (there's
     no equivalent conversational flow for email), so it's handled entirely
     inside this channel and writes to the DB directly, rather than being
     threaded through the generic NotificationChannel interface.

Uses raw HTTP calls (requests) rather than a heavier SDK — this bot only
needs sendMessage, getUpdates, and answerCallbackQuery.
"""

from pathlib import Path

import config
from channels.base import NotificationChannel

API_BASE = "https://api.telegram.org/bot{token}/{method}"
OFFSET_FILE = Path(__file__).resolve().parent.parent / ".telegram_offset"

ADD_CARD_TRIGGERS = {"/addcard", "/newcard"}
CANCEL_TRIGGERS = {"/cancel"}

class TelegramChannel(NotificationChannel):
    name = "telegram"

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        if not self.token or not self.chat_id:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env"
            )
        # chat_id -> {"step": "card_name" | "last4" | "payment_date" | "notify_days_before",
        #             "data": {...fields collected so far...}}
        # In-memory only: if the listener restarts mid-conversation, the user
        # just sends /addcard again. Not worth persisting for a single-user bot.
        self._pending_add: dict[int, dict] = {}