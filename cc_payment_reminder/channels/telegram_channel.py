#!/usr/bin/env python3
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
import db
from channels.base import Action, NotificationChannel, PaymentConfirmation

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

    def _get_offset(self) -> int:
        if OFFSET_FILE.exists():
            try:
                return int(OFFSET_FILE.read_text().strip())
            except ValueError:
                return 0
        return 0

    def _save_offset(self, offset: int):
        OFFSET_FILE.write_text(str(offset))

    def _start_add_card(self, chat_id: int) -> None:
        self._pending_add[chat_id] = {"step": "card_name", "data": {}}
        self._send_text(chat_id, "Let's add a new card. What's the card name? (e.g. HDFC Regalia)\n\nSend /cancel anytime to stop.")

    def _handle_add_card_reply(self, chat_id: int, text: str) -> None:
        state = self._pending_add[chat_id]
        step = state["step"]
        data = state["data"]

        if step == "card_name":
            card_name = text.strip()
            if not card_name:
                self._send_text(chat_id, "Card name can't be empty. What's the card name?")
                return
            data["card_name"] = card_name
            state["step"] = "last4"
            self._send_text(chat_id, "Last 4 digits of the card?")

        elif step == "last4":
            last4 = text.strip()
            if not (last4.isdigit() and len(last4) == 4):
                self._send_text(chat_id, "That needs to be exactly 4 digits. Last 4 digits of the card?")
                return
            data["last4"] = last4
            state["step"] = "payment_date"
            self._send_text(chat_id, "What day of the month is the bill due? (1-31)")

        elif step == "payment_date":
            raw = text.strip()
            if not (raw.isdigit() and 1 <= int(raw) <= 31):
                self._send_text(chat_id, "Please send a valid day of month (1-31). What day is the bill due?")
                return
            data["payment_date"] = int(raw)
            state["step"] = "notify_days_before"
            self._send_text(
                chat_id,
                "How many days before the due date should I start reminding you?\n"
                "Send a number, or 'skip' for the default (3).",
            )

        elif step == "notify_days_before":
            raw = text.strip().lower()
            if raw == "skip":
                notify_days_before = 3
            elif raw.isdigit():
                notify_days_before = int(raw)
            else:
                self._send_text(chat_id, "Please send a whole number of days, or 'skip' for the default (3).")
                return

            card_id = db.add_card(
                card_name=data["card_name"],
                last4=data["last4"],
                payment_date=data["payment_date"],
                notify_days_before=notify_days_before,
            )
            del self._pending_add[chat_id]
            self._send_text(
                chat_id,
                f"✅ Added #{card_id}: {data['card_name']} (••{data['last4']}), "
                f"due day {data['payment_date']} of the month, "
                f"reminding {notify_days_before} day(s) before.",
            )

    def poll_updates(self, timeout: int = 30) -> list[PaymentConfirmation]:
        """
        Long-poll getUpdates. Only processes updates from config.TELEGRAM_CHAT_ID
        (this bot's token is meant for a single owner) — anything else is
        silently ignored so a leaked bot token can't be used to add fake
        cards or mark real ones paid.
        """
        offset = self._get_offset()
        resp = requests.get(
            self._url("getUpdates"),
            params={"offset": offset, "timeout": timeout},
            timeout=timeout + 10,
        )
        resp.raise_for_status()
        data = resp.json()

        confirmations = []
        max_update_id = offset - 1

        for update in data.get("result", []):
            max_update_id = max(max_update_id, update["update_id"])

            if "callback_query" in update:
                cq = update["callback_query"]
                if str(cq.get("message", {}).get("chat", {}).get("id")) != str(self.chat_id):
                    continue
                callback_data = cq.get("data", "")
                if callback_data.startswith("paid:"):
                    card_id = int(callback_data.split(":", 1)[1])
                    confirmations.append(
                        PaymentConfirmation(card_id=card_id, card_name_hint=None, source_channel=self.name)
                    )
                    self.answer_callback(cq["id"])

            elif "message" in update:
                msg = update["message"]
                chat_id = msg.get("chat", {}).get("id")
                if str(chat_id) != str(self.chat_id):
                    continue

                text = msg.get("text", "").strip()
                lowered = text.lower()

                if lowered in ADD_CARD_TRIGGERS:
                    self._start_add_card(chat_id)
                elif chat_id in self._pending_add:
                    if lowered in CANCEL_TRIGGERS:
                        del self._pending_add[chat_id]
                        self._send_text(chat_id, "Cancelled.")
                    else:
                        self._handle_add_card_reply(chat_id, text)
                elif lowered.startswith("/paid"):
                    parts = text.split(maxsplit=1)
                    if len(parts) == 2:
                        confirmations.append(
                            PaymentConfirmation(card_id=None, card_name_hint=parts[1].strip(), source_channel=self.name)
                        )

        if max_update_id >= offset:
            self._save_offset(max_update_id + 1)

        return confirmations