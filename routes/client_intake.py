"""
Client intake API — multi-step wizard, OCR-assisted onboarding, AI helpers.

Business rules:
- OCR never auto-saves; admin must review and finalize.
- Drafts support partial completion.
- Finalize creates users + client profile tables.
"""
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status

from database import supabase
import auth as auth_utils
from limiter import limiter
from schemas_intake import (
    ApplyExtractionRequest,
    CaseClassifyRequest,
    CaseClassifyOut,
    ClientProfileOut,
    DuplicateCheckOut,
    DuplicateCheckRequest,
    IntakeDraftCreate,
    IntakeDraftOut,
    IntakeDraftUpdate,
    IntakeExtractionOut,
    IntakeFinalizeOut,
    IntakeSuggestionsOut,
    IntakeSuggestionsRequest,
    IntakeUploadOut,
    OcrMapFromTextRequest,
    OcrProcessRequest,
    PaginatedIntakeDraftsOut,
)
from services.intake_ai import build_suggestions, check_duplicates, classify_case
from services.intake_helpers import (
    build_full_name,
    draft_data_to_dict,
    generate_temp_password,
    merge_draft_data,
    normalize_phone,
    validate_finalize,
    validate_step,
)
from services.intake_ocr import format_extraction_response, process_text_ocr, process_upload_ocr
from services.intake_storage import upload_intake_file

router = APIRouter(prefix="/api/intake", tags=["Client Intake"])


def require_admin_or_attorney(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or attorney access required")
    return current_user


def _get_client_role_id() -> int:
    result = supabase.table("roles").select("id").eq("name", "client").execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Client role not found")
    return result.data[0]["id"]


def _log_ai(draft_id: Optional[int], action: str, performed_by: int, output: dict, inp: str = ""):
    try:
        supabase.table("intake_ai_logs").insert({
            "draft_id": draft_id,
            "action": action,
            "input_summary": inp[:500] if inp else None,
            "output_summary": output,
            "performed_by": performed_by,
        }).execute()
    except Exception:
        pass


# ── DRAFTS ────────────────────────────────────────────────────

@router.post("/drafts", response_model=IntakeDraftOut, status_code=status.HTTP_201_CREATED)
def create_draft(
    body: IntakeDraftCreate,
    user: dict = Depends(require_admin_or_attorney),
):
    draft_data = draft_data_to_dict(body.draft_data) if body.draft_data else {}
    if body.current_step >= 1 and draft_data:
        errs = validate_step(body.current_step, draft_data)
        if errs:
            raise HTTPException(status_code=400, detail={"errors": errs})

    row = supabase.table("client_intake_drafts").insert({
        "created_by": user["id"],
        "status": "draft",
        "current_step": body.current_step,
        "source": body.source,
        "draft_data": draft_data,
    }).execute()

    if not row.data:
        raise HTTPException(status_code=500, detail="Failed to create draft")
    return row.data[0]


@router.get("/drafts", response_model=PaginatedIntakeDraftsOut)
def list_drafts(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_admin_or_attorney),
):
    q = supabase.table("client_intake_drafts").select("id", count="exact").eq("created_by", user["id"])
    if status_filter:
        q = q.eq("status", status_filter)
    total = q.execute().count or 0

    query = (
        supabase.table("client_intake_drafts")
        .select("*")
        .eq("created_by", user["id"])
        .order("updated_at", desc=True)
    )
    if status_filter:
        query = query.eq("status", status_filter)
    items = query.range(skip, skip + limit - 1).execute().data or []
    page = (skip // limit) + 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 1,
    }


@router.get("/drafts/{draft_id}", response_model=IntakeDraftOut)
def get_draft(draft_id: int, user: dict = Depends(require_admin_or_attorney)):
    row = supabase.table("client_intake_drafts").select("*").eq("id", draft_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    d = row.data[0]
    if d.get("created_by") != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return d


@router.patch("/drafts/{draft_id}", response_model=IntakeDraftOut)
def update_draft(
    draft_id: int,
    body: IntakeDraftUpdate,
    user: dict = Depends(require_admin_or_attorney),
):
    existing = supabase.table("client_intake_drafts").select("*").eq("id", draft_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    d = existing.data[0]
    if d.get("created_by") != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if d.get("status") == "submitted":
        raise HTTPException(status_code=400, detail="Cannot edit a submitted draft")

    update_payload: dict = {}
    if body.current_step is not None:
        update_payload["current_step"] = body.current_step
    if body.status is not None:
        update_payload["status"] = body.status
    if body.draft_data is not None:
        merged = merge_draft_data(d.get("draft_data") or {}, draft_data_to_dict(body.draft_data))
        step = body.current_step or d.get("current_step", 1)
        errs = validate_step(step, merged)
        if errs:
            raise HTTPException(status_code=400, detail={"errors": errs})
        update_payload["draft_data"] = merged

    if not update_payload:
        return d

    result = supabase.table("client_intake_drafts").update(update_payload).eq("id", draft_id).execute()
    return result.data[0]


@router.delete("/drafts/{draft_id}")
def delete_draft(draft_id: int, user: dict = Depends(require_admin_or_attorney)):
    existing = supabase.table("client_intake_drafts").select("id, created_by").eq("id", draft_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    if existing.data[0].get("created_by") != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    supabase.table("client_intake_drafts").update({"status": "abandoned"}).eq("id", draft_id).execute()
    return {"message": "Draft abandoned"}


@router.post("/drafts/{draft_id}/validate")
def validate_draft_step(
    draft_id: int,
    step: int = Query(..., ge=1, le=4),
    user: dict = Depends(require_admin_or_attorney),
):
    d = get_draft(draft_id, user)
    errors = validate_step(step, d.get("draft_data") or {})
    return {"step": step, "valid": len(errors) == 0, "errors": errors}


# ── FILE UPLOADS ──────────────────────────────────────────────

@router.post("/uploads", response_model=IntakeUploadOut)
@limiter.limit("30/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    draft_id: Optional[int] = Form(None),
    category: str = Form("intake_form"),
    user: dict = Depends(require_admin_or_attorney),
):
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    _, public_url, upload_id = upload_intake_file(
        content,
        file.filename or "upload",
        content_type,
        user["id"],
        draft_id=draft_id,
        category=category,
    )
    row = supabase.table("intake_uploads").select("*").eq("id", upload_id).execute()
    return row.data[0]


# ── OCR WORKFLOW ──────────────────────────────────────────────

@router.post("/ocr/process", response_model=IntakeExtractionOut)
@limiter.limit("15/minute")
def run_ocr_process(
    request: Request,
    body: OcrProcessRequest,
    user: dict = Depends(require_admin_or_attorney),
):
    try:
        ext = process_upload_ocr(body.upload_id, body.draft_id, user["id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if body.draft_id:
        supabase.table("client_intake_drafts").update({
            "extraction_id": ext["id"],
            "intake_upload_id": body.upload_id,
            "source": "ocr",
        }).eq("id", body.draft_id).execute()

    return format_extraction_response(ext)


@router.post("/ocr/map-from-text", response_model=IntakeExtractionOut)
@limiter.limit("20/minute")
def ocr_map_from_text(
    request: Request,
    body: OcrMapFromTextRequest,
    user: dict = Depends(require_admin_or_attorney),
):
    ext = process_text_ocr(body.raw_text, body.draft_id, user["id"])
    return format_extraction_response(ext)


@router.get("/ocr/results/{extraction_id}", response_model=IntakeExtractionOut)
def get_extraction(extraction_id: int, user: dict = Depends(require_admin_or_attorney)):
    row = supabase.table("intake_extraction_results").select("*").eq("id", extraction_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return format_extraction_response(row.data[0])


@router.post("/ocr/apply", response_model=IntakeDraftOut)
def apply_extraction_to_draft(
    body: ApplyExtractionRequest,
    user: dict = Depends(require_admin_or_attorney),
):
    ext_row = supabase.table("intake_extraction_results").select("*").eq("id", body.extraction_id).execute()
    if not ext_row.data:
        raise HTTPException(status_code=404, detail="Extraction not found")
    ext = ext_row.data[0]
    mapped = ext.get("mapped_fields") or {}

    draft_row = supabase.table("client_intake_drafts").select("*").eq("id", body.draft_id).execute()
    if not draft_row.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    d = draft_row.data[0]
    if d.get("created_by") != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    merged = merge_draft_data(d.get("draft_data") or {}, mapped, overwrite=body.overwrite)
    result = supabase.table("client_intake_drafts").update({
        "draft_data": merged,
        "extraction_id": body.extraction_id,
        "source": "ocr",
    }).eq("id", body.draft_id).execute()

    supabase.table("intake_extraction_results").update({
        "reviewed": True,
        "reviewed_by": user["id"],
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", body.extraction_id).execute()

    _log_ai(body.draft_id, "apply_extraction", user["id"], {"extraction_id": body.extraction_id})
    return result.data[0]


# ── AI HELPERS ────────────────────────────────────────────────

@router.post("/ai/duplicates", response_model=DuplicateCheckOut)
def ai_duplicates(body: DuplicateCheckRequest, user: dict = Depends(require_admin_or_attorney)):
    matches = check_duplicates(
        body.first_name, body.middle_name, body.last_name, body.email, body.phone_number
    )
    _log_ai(None, "duplicate_check", user["id"], {"match_count": len(matches)})
    return {"has_duplicates": len(matches) > 0, "matches": matches}


@router.post("/ai/classify-case", response_model=CaseClassifyOut)
def ai_classify_case(body: CaseClassifyRequest, user: dict = Depends(require_admin_or_attorney)):
    return classify_case(body.notes, body.case_type)


@router.post("/ai/suggestions", response_model=IntakeSuggestionsOut)
def ai_suggestions(body: IntakeSuggestionsRequest, user: dict = Depends(require_admin_or_attorney)):
    suggestions, ready = build_suggestions(body.draft_data)
    return {"suggestions": suggestions, "is_ready_to_finalize": ready}


# ── FINALIZE (create client) ──────────────────────────────────

@router.post("/drafts/{draft_id}/finalize", response_model=IntakeFinalizeOut)
def finalize_draft(draft_id: int, user: dict = Depends(require_admin_or_attorney)):
    row = supabase.table("client_intake_drafts").select("*").eq("id", draft_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    d = row.data[0]
    if d.get("created_by") != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if d.get("status") == "submitted":
        raise HTTPException(status_code=400, detail="Draft already finalized")

    raw = d.get("draft_data") or {}
    validate_finalize(raw)

    personal = raw.get("personal") or {}
    contact = raw.get("contact") or {}
    valid_ids = raw.get("valid_ids") or {}
    case_info = raw.get("case_info") or {}

    email = contact.get("email")
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    full_name = personal.get("full_name") or build_full_name(
        personal.get("first_name", ""),
        personal.get("middle_name"),
        personal.get("last_name", ""),
        personal.get("suffix"),
    )
    temp_pw = raw.get("password") or generate_temp_password()
    role_id = _get_client_role_id()

    user_row = supabase.table("users").insert({
        "full_name": full_name,
        "email": email,
        "hashed_password": auth_utils.get_password_hash(temp_pw),
        "phone": normalize_phone(contact.get("phone_number", "")),
        "role_id": role_id,
        "is_active": True,
        "approval_status": "approved",
    }).execute()
    if not user_row.data:
        raise HTTPException(status_code=500, detail="Failed to create user account")
    new_user = user_row.data[0]
    uid = new_user["id"]

    supabase.table("clients").insert({
        "user_id": uid,
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
        "client_status": case_info.get("client_status", "prospect"),
        "priority_level": case_info.get("priority_level", "medium"),
        "tags": case_info.get("tags") or [],
        "referred_by": case_info.get("referred_by") or personal.get("referred_by"),
        "profile_photo_url": valid_ids.get("profile_photo_url"),
        "photo_uploaded_by": user["id"],
        "photo_metadata": valid_ids.get("photo_metadata") or {},
        "intake_completed_at": datetime.now(timezone.utc).isoformat(),
        "intake_completed_by": user["id"],
    }).execute()

    supabase.table("client_contact_info").insert({
        "user_id": uid,
        "email": email,
        "phone_number": contact.get("phone_number"),
        "alternate_phone": contact.get("alternate_phone"),
        "address": contact.get("address"),
        "barangay": contact.get("barangay"),
        "city": contact.get("city"),
        "province": contact.get("province"),
        "zip_code": contact.get("zip_code"),
        "country": contact.get("country", "Philippines"),
    }).execute()

    if valid_ids.get("primary_id_type"):
        supabase.table("client_valid_ids").insert({
            "user_id": uid,
            "id_type": valid_ids["primary_id_type"],
            "id_number": valid_ids["primary_id_number"],
            "id_image_url": valid_ids.get("primary_id_image_url"),
            "is_primary": True,
            "uploaded_by": user["id"],
        }).execute()
    if valid_ids.get("secondary_id_type") and valid_ids.get("secondary_id_number"):
        supabase.table("client_valid_ids").insert({
            "user_id": uid,
            "id_type": valid_ids["secondary_id_type"],
            "id_number": valid_ids["secondary_id_number"],
            "id_image_url": valid_ids.get("secondary_id_image_url"),
            "is_primary": False,
            "uploaded_by": user["id"],
        }).execute()

    if valid_ids.get("profile_photo_url"):
        supabase.table("client_photos").insert({
            "user_id": uid,
            "photo_url": valid_ids["profile_photo_url"],
            "uploaded_by": user["id"],
            "image_metadata": valid_ids.get("photo_metadata") or {},
            "is_current": True,
        }).execute()

    if case_info.get("case_type"):
        supabase.table("client_intake_cases").insert({
            "user_id": uid,
            "case_type": case_info["case_type"],
            "case_category": case_info.get("case_category"),
            "consultation_date": case_info.get("consultation_date"),
            "assigned_lawyer_id": case_info.get("assigned_lawyer_id"),
            "referred_by": case_info.get("referred_by"),
            "notes": case_info.get("notes"),
            "priority_level": case_info.get("priority_level", "medium"),
            "client_status": case_info.get("client_status", "prospect"),
            "tags": case_info.get("tags") or [],
        }).execute()

    supabase.table("client_intake_drafts").update({
        "status": "submitted",
        "user_id": uid,
    }).eq("id", draft_id).execute()

    try:
        from routes.audit_logs import log_action
        log_action(
            user["id"], user.get("full_name"), "intake_finalize", "client", uid,
            f"Client intake completed: {full_name} ({email})",
        )
    except Exception:
        pass

    _log_ai(draft_id, "finalize", user["id"], {"user_id": uid})

    return {
        "user_id": uid,
        "email": email,
        "full_name": full_name,
        "temporary_password": temp_pw if not raw.get("password") else None,
        "client_profile": {"user_id": uid, "full_name": full_name},
        "message": "Client created successfully. Share portal credentials securely.",
    }


# ── CLIENT PROFILE (post-intake) ──────────────────────────────

@router.get("/profiles/{user_id}", response_model=ClientProfileOut)
def get_client_profile(user_id: int, user: dict = Depends(require_admin_or_attorney)):
    u = supabase.table("users").select(
        "id, full_name, email, phone, approval_status"
    ).eq("id", user_id).execute()
    if not u.data:
        raise HTTPException(status_code=404, detail="User not found")

    client = supabase.table("clients").select("*").eq("user_id", user_id).execute()
    contact = supabase.table("client_contact_info").select("*").eq("user_id", user_id).execute()
    ids = supabase.table("client_valid_ids").select("*").eq("user_id", user_id).execute()
    cases = supabase.table("client_intake_cases").select("*").eq("user_id", user_id).execute()
    photos = supabase.table("client_photos").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

    return {
        "user_id": user_id,
        "full_name": u.data[0]["full_name"],
        "email": u.data[0]["email"],
        "phone": u.data[0].get("phone"),
        "approval_status": u.data[0].get("approval_status"),
        "personal": client.data[0] if client.data else None,
        "contact": contact.data[0] if contact.data else None,
        "valid_ids": ids.data or [],
        "intake_cases": cases.data or [],
        "photos": photos.data or [],
    }


@router.get("/id-types")
def list_id_types():
    from services.intake_helpers import ID_TYPES
    return {"id_types": ID_TYPES}


@router.get("/case-categories")
def list_case_categories():
    from services.intake_helpers import CASE_CATEGORIES
    return {"categories": CASE_CATEGORIES}
