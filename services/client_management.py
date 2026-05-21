"""Client Management — clients table as source of truth."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from database import get_supabase
from services.intake_storage import (
    normalize_upload_category,
    resolve_content_type,
    upload_intake_file,
)
from services.storage_urls import resolve_signed_url, resolve_upload_id_to_signed_url

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

CLIENT_UPLOAD_CATEGORIES = {
    "profile_photo",
    "valid_id_primary",
    "valid_id_secondary",
}


def require_staff_role(role: str) -> None:
    if role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin, attorney, secretary, or paralegal access required",
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_valid_ids_summary(user_id: int) -> Dict[str, Any]:
    """Aggregate client_valid_ids into frontend valid_ids shape with signed URLs."""
    rows = (
        get_supabase()
        .table("client_valid_ids")
        .select("id, id_type, id_number, id_image_url, is_primary")
        .eq("user_id", user_id)
        .order("is_primary", desc=True)
        .order("id")
        .execute()
    ).data or []

    out: Dict[str, Any] = {
        "primary_id_type": None,
        "primary_id_number": None,
        "primary_id_image_url": None,
        "secondary_id_type": None,
        "secondary_id_number": None,
        "secondary_id_image_url": None,
    }

    primary = next((r for r in rows if r.get("is_primary")), None)
    secondary = next((r for r in rows if not r.get("is_primary")), None)
    if not primary and rows:
        primary = rows[0]
        secondary = rows[1] if len(rows) > 1 else None
    elif primary and secondary and primary.get("id") == secondary.get("id"):
        secondary = None

    if primary:
        out["primary_id_type"] = primary.get("id_type")
        out["primary_id_number"] = primary.get("id_number")
        out["primary_id_image_url"] = resolve_signed_url(primary.get("id_image_url"))

    if secondary:
        out["secondary_id_type"] = secondary.get("id_type")
        out["secondary_id_number"] = secondary.get("id_number")
        out["secondary_id_image_url"] = resolve_signed_url(secondary.get("id_image_url"))

    return out


def _enrich_client_detail(row: dict) -> dict:
    row["profile_photo_url"] = resolve_signed_url(row.get("profile_photo_url"))
    uid = row.get("user_id")
    if uid:
        row["valid_ids"] = _build_valid_ids_summary(uid)
    else:
        row["valid_ids"] = {
            "primary_id_type": None,
            "primary_id_number": None,
            "primary_id_image_url": None,
            "secondary_id_type": None,
            "secondary_id_number": None,
            "secondary_id_image_url": None,
        }
    return row


def get_client_by_id(client_id: int, include_deleted: bool = False) -> dict:
    q = get_supabase().table("clients").select(DETAIL_COLS).eq("id", client_id)
    if not include_deleted:
        q = q.eq("is_deleted", False)
    result = q.execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    row = _attach_contact(result.data[0])
    return _enrich_client_detail(row)


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
    for item in items:
        item["profile_photo_url"] = resolve_signed_url(item.get("profile_photo_url"))
    page = (skip // limit) + 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 1,
    }


def search_clients(q: str, limit: int = 10) -> List[dict]:
    items = (
        get_supabase()
        .table("clients")
        .select("id, full_name, email, profile_photo_url, user_id")
        .eq("is_deleted", False)
        .or_(f"full_name.ilike.%{q}%,email.ilike.%{q}%")
        .order("full_name")
        .limit(limit)
        .execute()
    ).data or []
    for item in items:
        item["profile_photo_url"] = resolve_signed_url(item.get("profile_photo_url"))
    return items


def soft_delete_client(client_id: int) -> dict:
    row = get_client_by_id(client_id, include_deleted=True)
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

    # Store storage path when possible so reads can re-sign
    photo_ref = profile_photo_url
    from services.storage_urls import extract_storage_path
    photo_path = extract_storage_path(profile_photo_url)
    if photo_path:
        photo_ref = photo_path

    payload = {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "phone_number": phone_number,
        "profile_photo_url": photo_ref,
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


def _upsert_valid_id_row(
    user_id: int,
    *,
    is_primary: bool,
    id_type: Optional[str],
    id_number: Optional[str],
    image_url: Optional[str],
    uploaded_by: int,
) -> None:
    sb = get_supabase()
    existing = (
        sb.table("client_valid_ids")
        .select("id")
        .eq("user_id", user_id)
        .eq("is_primary", is_primary)
        .execute()
    )
    if not id_type and not id_number and not image_url:
        return

    payload = {
        "id_type": id_type or "Unknown",
        "id_number": id_number or "",
        "id_image_url": image_url,
        "uploaded_by": uploaded_by,
    }
    if existing.data:
        sb.table("client_valid_ids").update(payload).eq("id", existing.data[0]["id"]).execute()
    elif id_type and id_number:
        payload["user_id"] = user_id
        payload["is_primary"] = is_primary
        sb.table("client_valid_ids").insert(payload).execute()


def _apply_valid_ids_patch(uid: int, valid_ids: dict, staff_id: int) -> None:
    from services.storage_urls import extract_storage_path

    primary_url = valid_ids.get("primary_id_image_url")
    if valid_ids.get("primary_id_image_upload_id"):
        primary_url = resolve_upload_id_to_signed_url(int(valid_ids["primary_id_image_upload_id"]))
    if primary_url:
        path = extract_storage_path(primary_url)
        if path:
            primary_url = path

    secondary_url = valid_ids.get("secondary_id_image_url")
    if valid_ids.get("secondary_id_image_upload_id"):
        secondary_url = resolve_upload_id_to_signed_url(int(valid_ids["secondary_id_image_upload_id"]))
    if secondary_url:
        path = extract_storage_path(secondary_url)
        if path:
            secondary_url = path

    if any(
        valid_ids.get(k) is not None
        for k in (
            "primary_id_type", "primary_id_number", "primary_id_image_url",
            "primary_id_image_upload_id",
        )
    ):
        _upsert_valid_id_row(
            uid,
            is_primary=True,
            id_type=valid_ids.get("primary_id_type"),
            id_number=valid_ids.get("primary_id_number"),
            image_url=primary_url,
            uploaded_by=staff_id,
        )

    if any(
        valid_ids.get(k) is not None
        for k in (
            "secondary_id_type", "secondary_id_number", "secondary_id_image_url",
            "secondary_id_image_upload_id",
        )
    ):
        _upsert_valid_id_row(
            uid,
            is_primary=False,
            id_type=valid_ids.get("secondary_id_type"),
            id_number=valid_ids.get("secondary_id_number"),
            image_url=secondary_url,
            uploaded_by=staff_id,
        )


def patch_client(client_id: int, updates: dict, staff_id: int = 0) -> dict:
    row = get_client_by_id(client_id, include_deleted=True)
    uid = row.get("user_id")
    now = _now_iso()

    client_updates: Dict[str, Any] = {"updated_at": now}
    user_updates: Dict[str, Any] = {}
    contact_updates: Dict[str, Any] = {"updated_at": now}

    personal = updates.pop("personal", None) or {}
    valid_ids = updates.pop("valid_ids", None)

    field_map_client = {
        "full_name", "email", "phone_number", "profile_photo_url", "is_active",
        "first_name", "middle_name", "last_name", "suffix", "gender", "birth_date",
        "civil_status", "nationality", "place_of_birth", "occupation",
    }
    for key, val in list(updates.items()):
        if key in field_map_client and val is not None:
            client_updates[key] = val
        if key == "full_name" and val:
            user_updates["full_name"] = val
        if key == "email" and val:
            user_updates["email"] = val
        if key == "phone_number" and val:
            user_updates["phone"] = val

    for pk, pv in personal.items():
        if pv is not None and pk in field_map_client:
            client_updates[pk] = pv

    if updates.get("profile_photo_upload_id"):
        url = resolve_upload_id_to_signed_url(int(updates["profile_photo_upload_id"]))
        if url:
            from services.storage_urls import extract_storage_path
            client_updates["profile_photo_url"] = extract_storage_path(url) or url
    elif client_updates.get("profile_photo_url"):
        from services.storage_urls import extract_storage_path
        p = extract_storage_path(client_updates["profile_photo_url"])
        if p:
            client_updates["profile_photo_url"] = p

    contact_body = updates.get("contact") or {}
    contact_fields = ("address", "barangay", "city", "province", "zip_code", "country", "alternate_phone")
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

    if uid and valid_ids:
        _apply_valid_ids_patch(uid, valid_ids, staff_id)

    return get_client_by_id(client_id)


def upload_client_file(
    client_id: int,
    file_bytes: bytes,
    file_name: str,
    content_type: str,
    category: str,
    uploaded_by: int,
    user_role: str,
) -> Dict[str, Any]:
    """Upload for an existing client (no draft)."""
    client = get_client_by_id(client_id)
    cat = normalize_upload_category(category)
    if cat not in CLIENT_UPLOAD_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"category must be one of: {', '.join(sorted(CLIENT_UPLOAD_CATEGORIES))}",
        )

    storage_path, signed_url, upload_id = upload_intake_file(
        file_bytes,
        file_name,
        content_type,
        uploaded_by,
        draft_id=None,
        category=cat,
        user_role=user_role,
    )

    from services.storage_urls import extract_storage_path
    path_only = extract_storage_path(storage_path) or storage_path

    uid = client.get("user_id")
    if cat == "profile_photo":
        get_supabase().table("clients").update({
            "profile_photo_url": path_only,
            "updated_at": _now_iso(),
        }).eq("id", client_id).execute()
    elif uid and cat in ("valid_id_primary", "valid_id_secondary"):
        is_primary = cat == "valid_id_primary"
        existing = (
            get_supabase()
            .table("client_valid_ids")
            .select("id, id_type, id_number")
            .eq("user_id", uid)
            .eq("is_primary", is_primary)
            .execute()
        )
        if existing.data:
            get_supabase().table("client_valid_ids").update({
                "id_image_url": path_only,
                "uploaded_by": uploaded_by,
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            get_supabase().table("client_valid_ids").insert({
                "user_id": uid,
                "id_type": "Pending",
                "id_number": "Pending",
                "id_image_url": path_only,
                "is_primary": is_primary,
                "uploaded_by": uploaded_by,
            }).execute()

    fresh_url = resolve_signed_url(path_only) or signed_url
    return {"upload_id": upload_id, "id": upload_id, "url": fresh_url}
