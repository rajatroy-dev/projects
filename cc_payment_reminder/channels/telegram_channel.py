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
