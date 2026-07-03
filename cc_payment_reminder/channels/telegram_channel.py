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

import json
from pathlib import Path

import requests

import config
from channels.base import Action, NotificationChannel

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

    def _url(self, method: str) -> str:
        return API_BASE.format(token=self.token, method=method)

    def send(self, message: str, actions: list[Action]) -> None:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        if actions:
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": [[
                    {"text": a.label, "callback_data": a.action_id} for a in actions
                ]]
            })
        resp = requests.post(self._url("sendMessage"), data=payload, timeout=15)
        resp.raise_for_status()

    def _send_text(self, chat_id: int, text: str) -> None:
        resp = requests.post(
            self._url("sendMessage"),
            data={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        resp.raise_for_status()

    def answer_callback(self, callback_query_id: str, text: str = "Marked as paid ✅"):
        requests.post(
            self._url("answerCallbackQuery"),
            data={"callback_query_id": callback_query_id, "text": text},
            timeout=15,
        )