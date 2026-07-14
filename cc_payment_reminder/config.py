"""
Config loader. Reads settings from a .env file (simple KEY=VALUE format,
no external dependency needed) or from real environment variables.
Environment variables take precedence over .env file values.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def _load_dotenv(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


_dotenv_values = _load_dotenv(ENV_PATH)


def get(key: str, default=None, required: bool = False):
    value = os.environ.get(key, _dotenv_values.get(key, default))
    if required and not value:
        raise RuntimeError(
            f"Missing required config value: {key}. "
            f"Set it in {ENV_PATH} or as an environment variable."
        )
    return value


# Core settings
DB_PATH = get("BILL_DB_PATH", default=str(BASE_DIR / "bills.db"))

# Telegram channel settings
TELEGRAM_BOT_TOKEN = get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get("TELEGRAM_CHAT_ID")

# Which channels are active. Extend this list later, e.g. ["telegram", "email", "ntfy"]
ACTIVE_CHANNELS = [c.strip() for c in get("ACTIVE_CHANNELS", default="telegram").split(",") if c.strip()]

# Email channel settings (uses SES SMTP interface — see README for setup)
SES_SMTP_HOST = get("SES_SMTP_HOST", default="email-smtp.us-east-1.amazonaws.com")
SES_SMTP_PORT = int(get("SES_SMTP_PORT", default="587"))
SES_SMTP_USER = get("SES_SMTP_USER")
SES_SMTP_PASS = get("SES_SMTP_PASS")
EMAIL_FROM = get("EMAIL_FROM")          # e.g. bills@mailer-eventer.rajatroy.com
EMAIL_TO = get("EMAIL_TO")              # your personal inbox

# TOTP secret used by confirm_server.py to verify "Mark Paid" codes.
# Generate this once with totp_setup.py — treat it like a password.
TOTP_SECRET = get("TOTP_SECRET")

# Base URL for the confirm page, reachable only over Tailscale
# (e.g. https://bills.your-tailnet.ts.net or your own Tailscale-only subdomain)
CONFIRM_BASE_URL = get("CONFIRM_BASE_URL", default="http://localhost:5005")

# Local bind address/port for confirm_server.py
CONFIRM_SERVER_HOST = get("CONFIRM_SERVER_HOST", default="127.0.0.1")
CONFIRM_SERVER_PORT = int(get("CONFIRM_SERVER_PORT", default="5005"))
