"""Client Management — clients table as source of truth."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from database import get_supabase

STAFF_ROLES = ("admin", "attorney", "secretary", "paralegal")

LIST_COLS = (
    "id, user_id, full_name, email, phone_number, is_active, "
    "profile_photo_url, created_at, updated_at"
)

DETAIL_COLS = (
    "id, user_id, full_name, email, phone_number, is_active, is_deleted, "
    "profile_photo_url, first_name, middle_name, last_name, suffix, gender, "
    "birth_date, civil_status, nationality, place_of_birth, occupation, "
    "client_status, priority_level, tags, referred_by, created_at, updated_at"
)


def require_staff_role(role: str) -> None:
    if role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin, attorney, secretary, or paralegal access required",
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_client_by_id(client_id: int, include_deleted: bool = False) -> dict:
    q = get_supabase().table("clients").select(DETAIL_COLS).eq("id", client_id)
    if not include_deleted:
        q = q.eq("is_deleted", False)
    result = q.execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    row = result.data[0]
    return _attach_contact(row)


def _attach_contact(client_row: dict) -> dict:
    uid = client_row.get("user_id")
    if not uid:
        return client_row
    cci = (
        get_supabase()
        .table("client_contact_info")
        .select("*")
        .eq("user_id", uid)
        .execute()
    )
    if cci.data:
        client_row["contact"] = cci.data[0]
    return client_row


def list_clients(
    skip: int,
    limit: int,
    q: Optional[str] = None,
    is_deleted: bool = False,
) -> Dict[str, Any]:
    import math

    sb = get_supabase()
    count_q = sb.table("clients").select("id", count="exact").eq("is_deleted", is_deleted)
    data_q = (
        sb.table("clients")
        .select(LIST_COLS)
        .eq("is_deleted", is_deleted)
        .order("updated_at", desc=True)
    )
    if q:
        count_q = count_q.ilike("full_name", f"%{q}%")
        data_q = data_q.ilike("full_name", f"%{q}%")

    total = count_q.execute().count or 0
    items = data_q.range(skip, skip + limit - 1).execute().data or []
    page = (skip // limit) + 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 1,
    }


def search_clients(q: str, limit: int = 10) -> List[dict]:
    return (
        get_supabase()
        .table("clients")
        .select("id, full_name, email, profile_photo_url, user_id")
        .eq("is_deleted", False)
        .or_(f"full_name.ilike.%{q}%,email.ilike.%{q}%")
        .order("full_name")
        .limit(limit)
        .execute()
    ).data or []


def soft_delete_client(client_id: int) -> dict:
    row = get_client_by_id(client_id)
    now = _now_iso()
    get_supabase().table("clients").update({
        "is_deleted": True,
        "deleted_at": now,
        "updated_at": now,
    }).eq("id", client_id).execute()
    uid = row.get("user_id")
    if uid:
        get_supabase().table("users").update({"is_active": False}).eq("id", uid).execute()
    return {"message": f"Client {client_id} archived", "id": client_id}


def upsert_client_from_intake(
    user_id: int,
    full_name: str,
    email: str,
    phone_number: str,
    profile_photo_url: Optional[str],
    personal: dict,
    contact: dict,
    completed_by: int,
) -> dict:
    """Create or update clients row after intake finalize."""
    now = _now_iso()
    sb = get_supabase()
    existing = sb.table("clients").select("id").eq("user_id", user_id).execute()

    payload = {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "phone_number": phone_number,
        "profile_photo_url": profile_photo_url,
        "is_active": True,
        "is_deleted": False,
        "deleted_at": None,
        "first_name": personal.get("first_name"),
        "middle_name": personal.get("middle_name"),
        "last_name": personal.get("last_name"),
        "suffix": personal.get("suffix"),
        "gender": personal.get("gender"),
        "birth_date": personal.get("birth_date"),
        "civil_status": personal.get("civil_status"),
        "nationality": personal.get("nationality"),
        "place_of_birth": personal.get("place_of_birth"),
        "occupation": personal.get("occupation"),
        "client_status": "prospect",
        "priority_level": "medium",
        "tags": [],
        "referred_by": personal.get("referred_by"),
        "photo_uploaded_by": completed_by,
        "intake_completed_at": now,
        "intake_completed_by": completed_by,
        "updated_at": now,
    }

    if existing.data:
        cid = existing.data[0]["id"]
        sb.table("clients").update(payload).eq("id", cid).execute()
        client = sb.table("clients").select("id, user_id").eq("id", cid).execute().data[0]
    else:
        payload["created_at"] = now
        ins = sb.table("clients").insert(payload).execute()
        if not ins.data:
            raise HTTPException(status_code=500, detail="Failed to create client record")
        client = ins.data[0]

    return client


def patch_client(client_id: int, updates: dict) -> dict:
    row = get_client_by_id(client_id)
    uid = row.get("user_id")
    now = _now_iso()

    client_updates: Dict[str, Any] = {"updated_at": now}
    user_updates: Dict[str, Any] = {}
    contact_updates: Dict[str, Any] = {"updated_at": now}

    field_map_client = {
        "full_name", "email", "phone_number", "profile_photo_url", "is_active",
        "first_name", "middle_name", "last_name", "suffix", "gender", "birth_date",
        "civil_status", "nationality", "place_of_birth", "occupation",
    }
    for key, val in updates.items():
        if key in field_map_client and val is not None:
            client_updates[key] = val
        if key == "full_name" and val:
            user_updates["full_name"] = val
        if key == "email" and val:
            user_updates["email"] = val
        if key == "phone_number" and val:
            user_updates["phone"] = val

    contact_fields = ("address", "barangay", "city", "province", "zip_code", "country", "alternate_phone")
    contact_body = updates.get("contact") or {}
    for cf in contact_fields:
        if cf in contact_body and contact_body[cf] is not None:
            contact_updates[cf] = contact_body[cf]
    if updates.get("phone_number") is not None:
        contact_updates["phone_number"] = updates["phone_number"]
    if updates.get("email") is not None:
        contact_updates["email"] = updates["email"]

    sb = get_supabase()
    result = sb.table("clients").update(client_updates).eq("id", client_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update client")

    if uid and user_updates:
        sb.table("users").update(user_updates).eq("id", uid).execute()
    if uid and len(contact_updates) > 1:
        existing_cci = sb.table("client_contact_info").select("user_id").eq("user_id", uid).execute()
        if existing_cci.data:
            sb.table("client_contact_info").update(contact_updates).eq("user_id", uid).execute()
        else:
            contact_updates["user_id"] = uid
            sb.table("client_contact_info").insert(contact_updates).execute()

    return get_client_by_id(client_id)
