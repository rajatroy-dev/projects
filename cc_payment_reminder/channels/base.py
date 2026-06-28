"""
Notification channel abstraction.

Any new delivery mechanism (email, ntfy, SMS, ...) implements NotificationChannel.
notifier.py and listener.py only ever talk to this interface, never to a
specific provider — so adding a channel later means writing one new file here
and adding its name to config.ACTIVE_CHANNELS, nothing else changes.
"""
