#!/usr/bin/env python3
"""
CLI to manage credit card bill reminders.

Usage:
    python card_manager.py add
    python card_manager.py list
    python card_manager.py edit <id>
    python card_manager.py delete <id>
    python card_manager.py paid <id>
"""

import sys

import db

def cmd_add(args):
    card_name = input("Card name (e.g. HDFC Regalia): ").strip()
    last4 = input("Last 4 digits of card: ").strip()
    if not (last4.isdigit() and len(last4) == 4):
        print("Error: last4 must be exactly 4 digits.")
        sys.exit(1)

    while True:
        bill_date_raw = input("Bill payment date (day of month, 1-31): ").strip()
        if bill_date_raw.isdigit() and 1 <= int(bill_date_raw) <= 31:
            bill_date = int(bill_date_raw)
            break
        print("Please enter a valid day of month (1-31).")

    notify_raw = input("Notify how many days before due date? [default 3]: ").strip()
    notify_days_before = int(notify_raw) if notify_raw.isdigit() else 3

    card_id = db.add_card(card_name, last4, bill_date, notify_days_before)
    print(f"Added card #{card_id}: {card_name} (••{last4}), due on day {bill_date}, "
          f"notifying {notify_days_before} day(s) before.")