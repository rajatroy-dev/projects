"""
Email channel implementation.

Includes a link to confirm_server.py's confirm page, reachable only over
Tailscale network (see confirm_server.py and the README for the
deployment model). The link itself carries only a card_id — not a secret —
proof of identity comes from entering the current TOTP code on that page,
not from anything in the email itself. So even if this email is forwarded
or leaked, nothing in it lets someone mark a bill paid; they'd need both
network access to Tailscale-only confirm page AND authenticator
app.

Sends via the SES SMTP interface, fitting directly into an existing SES +
custom MAIL FROM domain setup (SMTP credentials only, no AWS IAM keys
needed on this box).

This channel does not implement poll_updates() — there's nothing to poll;
the base class's default (empty list) is used as-is.
"""
