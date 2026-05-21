"""
Re-seed Philippine valid ID type catalog (idempotent).

Run: python seed_valid_id_types.py
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
"""
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

PRIMARY = [
    ("Philippine Passport", 1),
    ("PhilSys National ID", 2),
    ("Driver's License", 3),
    ("UMID (Unified Multi-Purpose ID)", 4),
    ("PRC ID", 5),
    ("Postal ID", 6),
    ("Voter's ID", 7),
    ("SSS ID", 8),
    ("GSIS eCard", 9),
    ("Senior Citizen ID", 10),
    ("PWD ID", 11),
    ("OWWA ID", 12),
    ("OFW ID", 13),
]

SECONDARY = [
    ("TIN ID", 1),
    ("Barangay ID", 2),
    ("Company ID", 3),
    ("School ID", 4),
    ("Police Clearance", 5),
    ("NBI Clearance", 6),
    ("Birth Certificate", 7),
    ("Marriage Certificate", 8),
]


def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")

    sb = create_client(url, key)
    rows = []
    for name, order in PRIMARY:
        rows.append({"name": name, "category": "primary", "display_order": order, "is_active": True})
    for name, order in SECONDARY:
        rows.append({"name": name, "category": "secondary", "display_order": order, "is_active": True})

    for row in rows:
        sb.table("valid_id_types").upsert(row, on_conflict="name").execute()

    print(f"Seeded {len(rows)} valid ID types ({len(PRIMARY)} primary, {len(SECONDARY)} secondary).")


if __name__ == "__main__":
    main()
