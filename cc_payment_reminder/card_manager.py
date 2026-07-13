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
import argparse
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
    
def cmd_list(args):
    cards = db.list_cards()
    if not cards:
        print("No cards saved yet. Use 'add' to create one.")
        return
    for c in cards:
        print(f"[{c.id}] {c.display_name} — due day {c.bill_date} of month, "
              f"notify {c.notify_days_before}d before — status: {c.status} "
              f"(cycle {c.cycle_month})")


def cmd_edit(args):
    card = db.get_card(args.id)
    if not card:
        print(f"No card with id {args.id}")
        sys.exit(1)

    print(f"Editing {card.display_name}. Press Enter to keep current value.")
    card_name = input(f"Card name [{card.card_name}]: ").strip() or card.card_name
    last4 = input(f"Last 4 digits [{card.last4}]: ").strip() or card.last4
    bill_date_raw = input(f"Bill date [{card.bill_date}]: ").strip()
    bill_date = int(bill_date_raw) if bill_date_raw.isdigit() else card.bill_date
    notify_raw = input(f"Notify days before [{card.notify_days_before}]: ").strip()
    notify_days_before = int(notify_raw) if notify_raw.isdigit() else card.notify_days_before

    db.update_card(
        card.id,
        card_name=card_name,
        last4=last4,
        bill_date=bill_date,
        notify_days_before=notify_days_before,
    )
    print("Updated.")


def cmd_delete(args):
    card = db.get_card(args.id)
    if not card:
        print(f"No card with id {args.id}")
        sys.exit(1)
    confirm = input(f"Delete {card.display_name}? [y/N]: ").strip().lower()
    if confirm == "y":
        db.delete_card(card.id)
        print("Deleted.")
    else:
        print("Cancelled.")

def cmd_paid(args):
    card = db.get_card(args.id)
    if not card:
        print(f"No card with id {args.id}")
        sys.exit(1)
    db.mark_paid(card.id)
    print(f"Marked {card.display_name} as paid for cycle {card.cycle_month}.")


def main():
    db.init_db()

    parser = argparse.ArgumentParser(description="Manage credit card bill reminders.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="Add a new card").set_defaults(func=cmd_add)
    sub.add_parser("list", help="List all cards").set_defaults(func=cmd_list)

    p_edit = sub.add_parser("edit", help="Edit a card")
    p_edit.add_argument("id", type=int)
    p_edit.set_defaults(func=cmd_edit)

    p_delete = sub.add_parser("delete", help="Delete a card")
    p_delete.add_argument("id", type=int)
    p_delete.set_defaults(func=cmd_delete)

    p_paid = sub.add_parser("paid", help="Mark a card as paid for current cycle")
    p_paid.add_argument("id", type=int)
    p_paid.set_defaults(func=cmd_paid)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
