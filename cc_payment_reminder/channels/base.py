"""
Notification channel abstraction.

Any new delivery mechanism (email, ntfy, SMS, ...) implements NotificationChannel.
notifier.py and listener.py only ever talk to this interface, never to a
specific provider — so adding a channel later means writing one new file here
and adding its name to config.ACTIVE_CHANNELS, nothing else changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Action:
    """A single actionable button/link attached to a notification."""
    label: str          # e.g. "✅ Mark Paid"
    action_id: str       # opaque id the channel encodes into button/link, e.g. "paid:{card_id}"


@dataclass
class PaymentConfirmation:
    """Represents a user confirming a card is paid, from whatever channel."""
    card_id: int | None      # known if action_id encoded it directly
    card_name_hint: str | None  # known if user typed a free-text command instead
    source_channel: str


class NotificationChannel(ABC):
    name: str = "base"

    @abstractmethod
    def send(self, message: str, actions: list[Action]) -> None:
        """Send a notification with optional action buttons."""
        raise NotImplementedError

    def poll_updates(self) -> list[PaymentConfirmation]:
        """
        Return a list of new payment confirmations since last poll.
        Channels that don't support inbound interaction (e.g. one-way SMS)
        can simply not override this and it will return an empty list.
        """
        return []
