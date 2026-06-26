# Bill Reminder

Last month I missed a payment date for one of my credit cards. Because of my good track record I didn't incur a fine even though I made the payment after 3 days. I don't want to go through that again. As such this app.

It tracks credit card bill due dates and sends recurring hourly reminders
(Telegram + Email, with a pluggable abstraction to add more channels later)
until you mark the bill as paid.

## Stack
- **DB layer**: SQLite via [SQLModel](https://sqlmodel.tiangolo.com/) — `db.py`
- **Telegram**: raw Bot API calls via `requests` — `channels/telegram_channel.py`
- **Email**: SES SMTP + a link to a TOTP-gated confirm page — `channels/email_channel.py`, `confirm_server.py`

## ⚠️ Testing note
`confirm_server.py` uses FastAPI/pyotp/qrcode:
```bash
pip install -r requirements.txt --break-system-packages
python3 totp_setup.py                 # generates a secret + QR code
python3 confirm_server.py             # starts locally on :5005
# in another terminal, after adding a test card and getting its id:
curl "http://127.0.0.1:5005/confirm?card_id=1"   # should show the code-entry form
```

## Security note
Only the **last 4 digits** of each card are stored — never the full card
number.

## Setup

### 1. Install dependencies
```bash
cd bill-reminder
pip install -r requirements.txt --break-system-packages
```

### 2. Create a Telegram bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot`, follow prompts.
2. Copy the bot token.
3. Send any message to your new bot.
4. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and read `"chat":{"id": ...}` — that's your `TELEGRAM_CHAT_ID`.

### 3. Configure
```bash
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and email settings if using email
```

### 4. Add your cards
Message the bot **`/addcard`** (or `/newcard`) and answer the prompts: card name, last 4 digits, bill due day, and how many days before the due date to start reminding you (send `skip` for the default of 3). Send `/cancel` anytime to abort. This only works once the listener (step 6) is running, since it's driven by the same long-poll loop as `/paid`.

Or use the CLI, which has no dependency on the listener being up:
```bash
python3 card_manager.py add
```
Other commands: `list`, `edit <id>`, `delete <id>`, `paid <id>` (manual mark-paid, no dependencies).

### 5. Set up the hourly notifier (cron)
```bash
crontab -e
```
```
0 * * * * /usr/bin/python3 /home/youruser/bill-reminder/notifier.py >> /home/youruser/bill-reminder/notifier.log 2>&1
```

### 6. Set up the Telegram listener (systemd)
```bash
sudo cp systemd/bill-listener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bill-listener@youruser.service
```

## Email + TOTP confirm setup

### 1. SES SMTP credentials
AWS SES console → **Account dashboard → SMTP settings → Create SMTP credentials** (not your regular IAM keys). Fill `SES_SMTP_USER`/`SES_SMTP_PASS`/`EMAIL_FROM`/`EMAIL_TO` in `.env`.

### 2. Generate a TOTP secret
```bash
python3 totp_setup.py
```
This prints a secret and saves `totp_qr.png` — scan the QR code into an authenticator app (Google Authenticator, Aegis, etc.), then add the printed `TOTP_SECRET=...` line to `.env`. **Treat this secret like a password** — anyone who has it can mint valid codes.

### 3. Run confirm_server.py, exposed only via Tailscale
```bash
sudo cp systemd/confirm-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now confirm-server@youruser.service
```

This binds locally to `127.0.0.1:5005`. Route a Tailscale-only hostname to it — this app has **no built-in exposure protection** (no rate limiting, no HTTPS of its own), because it's designed to sit behind that existing private-network boundary, not the public internet. Set `CONFIRM_BASE_URL` in `.env` to that Tailscale-only hostname.

## How it works
- **notifier.py** (hourly cron): for unpaid cards in their notify window, sends a reminder through every channel in `ACTIVE_CHANNELS`.
- **Telegram**: message includes a button like **"✅ Mark 1234 as paid"** — tapping it fires a callback handled by `listener.py` (the one persistent process for Telegram). Typing `/paid 1234` or `/paid HDFC` does the same thing. Sending `/addcard` walks you through adding a new card without touching the command line (see step 4 above). Both only respond to messages from `TELEGRAM_CHAT_ID` — anyone else messaging the bot is ignored.
- **Email**: message includes a "Mark Paid" link carrying only the card's id (not a secret). Opening it (Tailscale required) shows a code-entry page; entering your current TOTP code marks the card paid. No per-email token — the same mechanism works indefinitely since verification is stateless.
- Once paid, hourly reminders stop for that cycle; the card auto-resets to `unpaid` when the calendar rolls into a new month.

## Marking a bill as paid
- **Telegram**: tap the button, or type `/paid 1234`
- **Email**: click the link (Tailscale only), enter your authenticator code
- **CLI (always works)**: `python3 card_manager.py paid <id>`

## Why TOTP instead of a per-email link token
A per-email token needs an expiry, single-use tracking, and a DB table to manage all that. TOTP verification is stateless — the code is valid proof on its own, checked against a secret set up once. Combined with restricting the confirm page to Tailscale network, this needs meaningfully less moving infrastructure while still requiring two independent things to mark a bill paid: network access to a private host, and possession of authenticator app.

## Adding another channel later (e.g. ntfy)
1. Create `channels/ntfy_channel.py` implementing `NotificationChannel`.
2. Register it in `channels/registry.py`'s `_CHANNEL_CLASSES` dict.
3. Add `ntfy` to `ACTIVE_CHANNELS` in `.env`.

No changes needed in `notifier.py`, `listener.py`, or the DB layer.