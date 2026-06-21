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