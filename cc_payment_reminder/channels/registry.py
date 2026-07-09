"""
Maps channel names (from config.ACTIVE_CHANNELS) to their implementation.
Adding a new channel later = add one line here + implement the class.
"""
import config
from channels.base import NotificationChannel
from channels.telegram_channel import TelegramChannel
from channels.email_channel import EmailChannel

_CHANNEL_CLASSES = {
    "telegram": TelegramChannel,
    "email": EmailChannel,
    # "ntfy": NtfyChannel,     # future
}


def get_active_channels() -> list[NotificationChannel]:
    channels = []
    for name in config.ACTIVE_CHANNELS:
        cls = _CHANNEL_CLASSES.get(name)
        if cls is None:
            print(f"[warn] Unknown channel '{name}' in ACTIVE_CHANNELS, skipping.")
            continue
        channels.append(cls())
    return channels
