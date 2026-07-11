"""One-time setup script.

Run this ONCE after applying schema.sql to create your login accounts with
secure hashed PINs. Safe to re-run: it won't create duplicates.

    # local:
    DATABASE_URL="postgresql://..." python seed.py

It prints the starting PINs. Change them in Settings after first login.
"""
import os
from db import fetch_one, fetch_all, execute
from auth import hash_pin

COMPANY_ID = 1

# name, role, starting PIN
DEFAULT_ACCOUNTS = [
    ("Admin",    "admin",    "246810"),
    ("Dispatch", "dispatch", "135790"),
    ("Billing",  "ar",       "112233"),
]
DEFAULT_DRIVER_PIN = "1234"


def ensure_company():
    row = fetch_one("SELECT id FROM companies WHERE id=:id", {"id": COMPANY_ID})
    if not row:
        execute(
            "INSERT INTO companies (id, name, tagline, primary_color) "
            "VALUES (:id, :name, :tag, :color)",
            {"id": COMPANY_ID, "name": "Rick's Oilfield Hauling",
             "tag": "Oilfield Hauling · Digital Field Tickets", "color": "#8B5CF6"},
        )
        print(f"Created company #{COMPANY_ID}")


def ensure_account(name, role, pin):
    row = fetch_one(
        "SELECT id, pin_hash FROM users WHERE company_id=:cid AND name=:name AND role=:role",
        {"cid": COMPANY_ID, "name": name, "role": role},
    )
    if row is None:
        execute(
            "INSERT INTO users (company_id, name, role, pin_hash, active) "
            "VALUES (:cid, :name, :role, :ph, TRUE)",
            {"cid": COMPANY_ID, "name": name, "role": role, "ph": hash_pin(pin)},
        )
        print(f"  + created {role:9s} '{name}'  PIN: {pin}")
    elif not row[1]:
        execute("UPDATE users SET pin_hash=:ph WHERE id=:id",
                {"ph": hash_pin(pin), "id": row[0]})
        print(f"  ~ set PIN for existing {role} '{name}'  PIN: {pin}")
    else:
        print(f"  = {role} '{name}' already has a PIN (unchanged)")


def secure_existing_drivers():
    drivers = fetch_all(
        "SELECT id, name FROM users WHERE company_id=:cid AND role='driver' AND pin_hash IS NULL",
        {"cid": COMPANY_ID},
    )
    for did, dname in drivers:
        execute("UPDATE users SET pin_hash=:ph WHERE id=:id",
                {"ph": hash_pin(DEFAULT_DRIVER_PIN), "id": did})
        print(f"  ~ secured driver '{dname}'  starting PIN: {DEFAULT_DRIVER_PIN}")


def main():
    if not os.environ.get("DATABASE_URL"):
        print("Set DATABASE_URL first, e.g.:  DATABASE_URL='postgresql://...' python seed.py")
        return
    print("Setting up TicketDrop accounts...\n")
    ensure_company()
    for name, role, pin in DEFAULT_ACCOUNTS:
        ensure_account(name, role, pin)
    secure_existing_drivers()
    print("\nDone. Sign in with any account above, then change PINs in Settings.")


if __name__ == "__main__":
    main()
