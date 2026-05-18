"""
Seed script — inserts ~50 sample records into every table.
Run: python seed.py
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
"""

import os
import random
import math
from datetime import date, timedelta, datetime
from decimal import Decimal
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
if not url or not key:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")

sb = create_client(url, key)

from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = pwd_ctx.hash("Password123!")

# ── helpers ──────────────────────────────────────────────────

def rand_date(start_days_ago=365, end_days_ahead=90) -> str:
    base = date.today()
    delta = random.randint(-start_days_ago, end_days_ahead)
    return str(base + timedelta(days=delta))

def rand_past_date(days=365) -> str:
    base = date.today()
    return str(base - timedelta(days=random.randint(1, days)))

def rand_future_date(days=180) -> str:
    base = date.today()
    return str(base + timedelta(days=random.randint(1, days)))

FIRST_NAMES = ["Maria", "Jose", "Juan", "Ana", "Pedro", "Rosa", "Miguel", "Carmen",
               "Luis", "Elena", "Carlos", "Linda", "David", "Grace", "Mark", "Faith",
               "James", "Hope", "Robert", "Joy", "Michael", "Love", "John", "Mercy",
               "Richard", "Gloria", "Henry", "Luz", "Edward", "Paz"]
LAST_NAMES  = ["Santos", "Reyes", "Cruz", "Garcia", "Torres", "Flores", "Gomez",
               "Lopez", "Martinez", "Perez", "Rivera", "Dela Cruz", "Bautista",
               "Ramos", "Aquino", "Salazar", "Mendoza", "Lim", "Tan", "Chua",
               "Sy", "Go", "Chan", "Wong", "Ng", "Lee", "Kim", "Villanueva"]

PRACTICE_AREAS = ["Family Law", "Criminal Defense", "Corporate Law", "Real Estate",
                  "Labor Law", "Civil Litigation", "Immigration", "Tax Law",
                  "Intellectual Property", "Environmental Law"]
CASE_TYPES = ["Civil", "Criminal", "Family", "Corporate", "Real Estate",
              "Labor", "Immigration", "Tax", "IP", "Environmental"]
COURTS = ["RTC Manila Branch 1", "RTC Makati Branch 3", "MTC Quezon City",
          "RTC Pasig Branch 7", "Court of Appeals", "Supreme Court",
          "NLRC Manila", "RTC Paranaque Branch 2"]
JUDGES = ["Hon. Antonio Reyes", "Hon. Maria Santos", "Hon. Roberto Cruz",
          "Hon. Elena Garcia", "Hon. Carlos Torres", "Hon. Linda Flores"]
DOC_TYPES = ["pdf", "docx", "jpg", "png", "xlsx"]
NOTIF_TYPES = ["case", "appointment", "message", "document", "invoice", "system"]
TIMES = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "01:00 PM",
         "02:00 PM", "03:00 PM", "04:00 PM"]
CASE_STATUSES = ["open", "in_progress", "review", "closed"]
APPT_STATUSES = ["pending", "confirmed", "completed", "cancelled"]
INV_STATUSES  = ["unpaid", "paid", "overdue", "cancelled"]

def rand_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_email(name: str, idx: int) -> str:
    slug = name.lower().replace(" ", ".").replace("ñ", "n")
    return f"{slug}{idx}@example.com"

# ── 1. Roles ─────────────────────────────────────────────────
print("Checking roles…")
roles_res = sb.table("roles").select("id, name").execute()
role_map = {r["name"]: r["id"] for r in (roles_res.data or [])}
if not role_map:
    print("  No roles found — run migration_roles.sql first.")
    raise SystemExit(1)
print(f"  Found roles: {list(role_map.keys())}")

# ── 2. Users ─────────────────────────────────────────────────
print("Seeding users…")
existing_emails = {u["email"] for u in (sb.table("users").select("email").execute().data or [])}

admin_id = None
attorney_ids = []
client_ids = []

for i in range(1, 6):
    name = rand_name()
    email = f"attorney{i}@lawfirm.com"
    if email not in existing_emails:
        res = sb.table("users").insert({
            "full_name": f"Atty. {name}",
            "email": email,
            "hashed_password": DEFAULT_PASSWORD,
            "role_id": role_map.get("attorney"),
            "phone": f"09{random.randint(100000000, 999999999)}",
            "is_active": True,
            "approval_status": "approved",
            "specialization": random.choice(PRACTICE_AREAS),
        }).execute()
        if res.data:
            attorney_ids.append(res.data[0]["id"])
    else:
        row = sb.table("users").select("id").eq("email", email).execute()
        if row.data:
            attorney_ids.append(row.data[0]["id"])

if not admin_id:
    admin_email = "admin@lawfirm.com"
    if admin_email not in existing_emails:
        res = sb.table("users").insert({
            "full_name": "Admin User",
            "email": admin_email,
            "hashed_password": DEFAULT_PASSWORD,
            "role_id": role_map.get("admin"),
            "phone": "09000000000",
            "is_active": True,
            "approval_status": "approved",
        }).execute()
        if res.data:
            admin_id = res.data[0]["id"]
    else:
        row = sb.table("users").select("id").eq("email", admin_email).execute()
        if row.data:
            admin_id = row.data[0]["id"]

for i in range(1, 46):
    name = rand_name()
    email = f"client{i}@example.com"
    if email not in existing_emails:
        res = sb.table("users").insert({
            "full_name": name,
            "email": email,
            "hashed_password": DEFAULT_PASSWORD,
            "role_id": role_map.get("client"),
            "phone": f"09{random.randint(100000000, 999999999)}",
            "is_active": True,
            "approval_status": "approved",
        }).execute()
        if res.data:
            client_ids.append(res.data[0]["id"])
    else:
        row = sb.table("users").select("id").eq("email", email).execute()
        if row.data:
            client_ids.append(row.data[0]["id"])

if not attorney_ids:
    attorney_ids = [u["id"] for u in sb.table("users").select("id").eq("role_id", role_map.get("attorney", 0)).execute().data or []]
if not client_ids:
    client_ids = [u["id"] for u in sb.table("users").select("id").eq("role_id", role_map.get("client", 0)).execute().data or []]

print(f"  Attorneys: {len(attorney_ids)}, Clients: {len(client_ids)}")

# ── 3. Cases ─────────────────────────────────────────────────
print("Seeding cases…")
for i in range(1, 51):
    case_number = f"CASE-{2024 + random.randint(0,1)}-{str(i).zfill(4)}"
    existing = sb.table("cases").select("id").eq("case_number", case_number).execute()
    if existing.data:
        continue
    client = random.choice(client_ids) if client_ids else None
    attorney = random.choice(attorney_ids) if attorney_ids else None
    sb.table("cases").insert({
        "case_number": case_number,
        "case_name": f"{random.choice(CASE_TYPES)} Case #{i} - {rand_name()} vs. {rand_name()}",
        "case_type": random.choice(CASE_TYPES),
        "description": f"Sample case description for case #{i}. This involves legal proceedings related to {random.choice(PRACTICE_AREAS)}.",
        "status": random.choice(CASE_STATUSES),
        "client_id": client,
        "attorney_id": attorney,
        "next_hearing_date": rand_future_date(120) if random.random() > 0.3 else None,
        "next_hearing_time": random.choice(TIMES) if random.random() > 0.3 else None,
        "court": random.choice(COURTS),
        "judge": random.choice(JUDGES),
        "filed_date": rand_past_date(400),
    }).execute()

case_ids = [c["id"] for c in (sb.table("cases").select("id").execute().data or [])]
print(f"  Cases in DB: {len(case_ids)}")

# ── 4. Appointments ───────────────────────────────────────────
print("Seeding appointments…")
for i in range(1, 51):
    client = random.choice(client_ids) if client_ids else None
    attorney = random.choice(attorney_ids) if attorney_ids else None
    pref_date = rand_date(30, 60)
    sb.table("appointments").insert({
        "full_name": rand_name(),
        "email": f"appt{i}@example.com",
        "phone": f"09{random.randint(100000000, 999999999)}",
        "practice_area": random.choice(PRACTICE_AREAS),
        "message": f"I need legal assistance regarding {random.choice(PRACTICE_AREAS)}. Please schedule a consultation.",
        "preferred_date": pref_date,
        "preferred_time": random.choice(TIMES),
        "appointment_type": random.choice(["onsite", "online"]),
        "status": random.choice(APPT_STATUSES),
        "user_id": client,
        "attorney_id": attorney,
        "notes": "Confirmed via phone call." if random.random() > 0.5 else None,
    }).execute()

# ── 5. Documents ──────────────────────────────────────────────
print("Seeding documents…")
for i in range(1, 51):
    case = random.choice(case_ids) if case_ids else None
    uploader = random.choice(attorney_ids) if attorney_ids else None
    doc_type = random.choice(DOC_TYPES)
    sb.table("documents").insert({
        "title": f"Document-{i:03d}.{doc_type}",
        "file_url": f"https://storage.supabase.co/documents/doc_{i}.{doc_type}",
        "file_type": doc_type,
        "file_size": random.randint(10240, 5242880),
        "case_id": case,
        "uploaded_by": uploader,
        "description": f"Legal document #{i} for case proceedings.",
        "is_confidential": random.random() > 0.7,
    }).execute()

# ── 6. Messages ───────────────────────────────────────────────
print("Seeding messages…")
for i in range(1, 51):
    sender = random.choice(client_ids + attorney_ids) if client_ids else None
    recipient = random.choice(attorney_ids + client_ids) if attorney_ids else None
    if sender == recipient and recipient:
        recipient = attorney_ids[0] if attorney_ids else None
    case = random.choice(case_ids) if case_ids and random.random() > 0.4 else None
    sb.table("messages").insert({
        "sender_id": sender,
        "recipient_id": recipient,
        "case_id": case,
        "subject": random.choice(["Case Update", "Hearing Schedule", "Document Request", "Invoice Query", "General Inquiry"]),
        "body": f"This is message #{i}. Please review the attached information and respond at your earliest convenience.",
        "is_read": random.random() > 0.5,
    }).execute()

# ── 7. Invoices ───────────────────────────────────────────────
print("Seeding invoices…")
for i in range(1, 51):
    inv_num = f"INV-2025-{str(i).zfill(4)}"
    existing = sb.table("invoices").select("id").eq("invoice_number", inv_num).execute()
    if existing.data:
        continue
    client = random.choice(client_ids) if client_ids else None
    case = random.choice(case_ids) if case_ids and random.random() > 0.3 else None
    amount = round(random.uniform(5000, 150000), 2)
    tax = round(amount * 0.12, 2)
    total = round(amount + tax, 2)
    inv_status = random.choice(INV_STATUSES)
    sb.table("invoices").insert({
        "invoice_number": inv_num,
        "client_id": client,
        "case_id": case,
        "amount": str(amount),
        "tax": str(tax),
        "total": str(total),
        "status": inv_status,
        "due_date": rand_future_date(60),
        "paid_date": rand_past_date(30) if inv_status == "paid" else None,
        "notes": "Legal services rendered." if random.random() > 0.5 else None,
    }).execute()

# ── 8. Notifications ──────────────────────────────────────────
print("Seeding notifications…")
all_user_ids = client_ids + attorney_ids + ([admin_id] if admin_id else [])
for i in range(1, 51):
    uid = random.choice(all_user_ids) if all_user_ids else None
    notif_type = random.choice(NOTIF_TYPES)
    sb.table("notifications").insert({
        "user_id": uid,
        "type": notif_type,
        "title": f"Notification #{i}: {notif_type.title()} Update",
        "body": f"You have a new {notif_type} activity. Please check your dashboard for details.",
        "is_read": random.random() > 0.6,
        "link": f"/dashboard/{notif_type}s",
    }).execute()

# ── 9. Audit Logs ─────────────────────────────────────────────
print("Seeding audit logs…")
ACTIONS = ["login", "logout", "create_case", "update_case", "view_case",
           "upload_document", "send_message", "update_profile", "create_appointment",
           "update_appointment", "mark_notification_read", "create_invoice"]
ENTITY_TYPES = ["case", "appointment", "document", "message", "invoice", "user", "notification"]

for i in range(1, 51):
    uid = random.choice(all_user_ids) if all_user_ids else None
    action = random.choice(ACTIONS)
    entity_type = random.choice(ENTITY_TYPES)
    user_name = None
    if uid:
        row = sb.table("users").select("full_name").eq("id", uid).execute()
        user_name = row.data[0]["full_name"] if row.data else None
    sb.table("audit_logs").insert({
        "user_id": uid,
        "user_name": user_name,
        "action": action,
        "entity_type": entity_type,
        "entity_id": random.choice(case_ids) if case_ids else None,
        "description": f"User performed '{action}' on {entity_type} record.",
        "ip_address": f"192.168.1.{random.randint(1, 254)}",
    }).execute()

print("\n✅  Seeding complete!")
print("   Login: admin@lawfirm.com / Password123!")
print("   Login: attorney1@lawfirm.com / Password123!")
print("   Login: client1@example.com / Password123!")
