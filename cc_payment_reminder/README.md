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