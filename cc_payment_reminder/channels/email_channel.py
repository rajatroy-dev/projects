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

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from channels.base import Action, NotificationChannel

class EmailChannel(NotificationChannel):
    name = "email"

    def __init__(self):
        required = {
            "SES_SMTP_USER": config.SES_SMTP_USER,
            "SES_SMTP_PASS": config.SES_SMTP_PASS,
            "EMAIL_FROM": config.EMAIL_FROM,
            "EMAIL_TO": config.EMAIL_TO,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise RuntimeError(
                f"Email channel missing required config: {', '.join(missing)}. "
                f"Set these in .env."
            )
        
    def send(self, message: str, actions: list[Action]) -> None:
        card_id = None
        for a in actions:
            if a.action_id.startswith("paid:"):
                card_id = int(a.action_id.split(":", 1)[1])
                break

        confirm_html = ""
        confirm_text = ""
        if card_id is not None:
            confirm_url = f"{config.CONFIRM_BASE_URL}/confirm?card_id={card_id}"
            confirm_text = f"\n\nMark paid (Tailscale only, needs your authenticator code): {confirm_url}"
            confirm_html = f"""
            <p style="margin-top: 20px;">
              <a href="{confirm_url}"
                 style="background-color:#2e7d32;color:#ffffff;padding:12px 24px;
                        text-decoration:none;border-radius:6px;font-weight:bold;
                        display:inline-block;">
                ✅ Mark Paid
              </a>
            </p>
            <p style="color:#888;font-size:12px;">
              Only reachable on your Tailscale network. You'll be asked for your authenticator code.
            </p>
            """

        text_body = message + confirm_text
        html_body = f"""
        <html><body style="font-family: sans-serif; color:#222;">
          <pre style="white-space:pre-wrap;font-family:inherit;">{message}</pre>
          {confirm_html}
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Bill Payment Reminder"
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(config.SES_SMTP_HOST, config.SES_SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SES_SMTP_USER, config.SES_SMTP_PASS)
            server.sendmail(config.EMAIL_FROM, [config.EMAIL_TO], msg.as_string())