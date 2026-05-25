from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils
import math
from datetime import date

router = APIRouter(prefix="/api/cases", tags=["Cases"])

# List view excludes description — kept in detail endpoint
_CASE_LIST_COLS = "id,case_number,case_name,case_type,status,client_id,attorney_id,court,judge,filed_date,closed_date,created_at"


def _sync_dashboard_stats(user_id: int, role: str):
    """Update dashboard_stats table for a specific user."""
    try:
        # Compute stats for the user
        if role == "client":
            cases_res = supabase.table("cases").select("id,status").eq("client_id", user_id).execute()
        elif role == "attorney":
            cases_res = supabase.table("cases").select("id,status").eq("attorney_id", user_id).execute()
        else:
            cases_res = supabase.table("cases").select("id,status").execute()

        all_cases = cases_res.data or []
        total_cases = len(all_cases)
        cases_in_progress = sum(1 for c in all_cases if c.get("status") == "in_progress")
        cases_review = sum(1 for c in all_cases if c.get("status") == "review")
        cases_closed = sum(1 for c in all_cases if c.get("status") == "closed")
        cases_open = sum(1 for c in all_cases if c.get("status") == "open")
        active_cases = cases_in_progress + cases_review + cases_open

        today = str(date.today())
        if role == "client":
            r = supabase.table("appointments").select("id", count="exact").eq("user_id", user_id).eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
            case_ids = [c["id"] for c in all_cases]
            if case_ids:
                r = supabase.table("documents").select("id", count="exact").in_("case_id", case_ids).execute()
                total_documents = r.count or 0
            else:
                total_documents = 0
            r = supabase.table("invoices").select("id", count="exact").eq("client_id", user_id).eq("status", "unpaid").execute()
            unpaid_invoices = r.count or 0
        elif role == "attorney":
            r = supabase.table("appointments").select("id", count="exact").eq("attorney_id", user_id).eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
            total_documents = 0
            unpaid_invoices = 0
        else:
            r = supabase.table("appointments").select("id", count="exact").eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
            r = supabase.table("documents").select("id", count="exact").execute()
            total_documents = r.count or 0
            r = supabase.table("invoices").select("id", count="exact").eq("status", "unpaid").execute()
            unpaid_invoices = r.count or 0

        r = supabase.table("messages").select("id", count="exact").eq("recipient_id", user_id).eq("is_read", False).execute()
        unread_messages = r.count or 0
        r = supabase.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
        unread_notifications = r.count or 0

        # Update or insert dashboard_stats
        stats_data = {
            "active_cases": active_cases,
            "total_cases": total_cases,
            "cases_open": cases_open,
            "cases_in_progress": cases_in_progress,
            "cases_review": cases_review,
            "cases_closed": cases_closed,
            "upcoming_appointments": upcoming_appointments,
            "unpaid_invoices": unpaid_invoices,
            "total_documents": total_documents,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
        }

        existing = supabase.table("dashboard_stats").select("id").eq("user_id", user_id).execute()
        if existing.data:
            supabase.table("dashboard_stats").update(stats_data).eq("user_id", user_id).execute()
        else:
            stats_data["user_id"] = user_id
            supabase.table("dashboard_stats").insert(stats_data).execute()
    except Exception:
        pass  # Don't fail the main operation if stats sync fails


@router.post("", response_model=schemas.CaseOut, summary="Create a new case (admin/attorney)")
def create_case(
    case: schemas.CaseCreate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only attorneys or admins can create cases")

    data = {
        "case_number": case.case_number,
        "case_name": case.case_name,
        "case_type": case.case_type,
        "description": case.description,
        "status": case.status or "open",
        "client_id": case.client_id,
        "attorney_id": case.attorney_id,
        "court": case.court,
        "judge": case.judge,
        "filed_date": str(case.filed_date) if case.filed_date else None,
    }
    result = supabase.table("cases").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create case")
    
    # Sync dashboard_stats for client and attorney
    if case.client_id:
        _sync_dashboard_stats(case.client_id, "client")
    if case.attorney_id:
        _sync_dashboard_stats(case.attorney_id, "attorney")
    
    return result.data[0]


@router.get("", response_model=schemas.PaginatedCasesOut, summary="Get all cases (admin) or my cases (client/attorney)")
def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    case_status: Optional[str] = Query(None, alias="status"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    role = current_user.get("role", "client")
    cols = "id,case_number,case_name,case_type,status,client_id,attorney_id,court,judge,filed_date,closed_date,created_at"

    # Count query
    count_q = supabase.table("cases").select("id", count="exact")
    if role == "client":
        count_q = count_q.eq("client_id", current_user["id"])
    elif role == "attorney":
        count_q = count_q.eq("attorney_id", current_user["id"])
    if case_status:
        count_q = count_q.eq("status", case_status)
    if date_from:
        count_q = count_q.gte("filed_date", date_from)
    if date_to:
        count_q = count_q.lte("filed_date", date_to)
    total = count_q.execute().count or 0

    # Data query
    query = supabase.table("cases").select(_CASE_LIST_COLS).order("created_at", desc=True).range(skip, skip + limit - 1)
    if role == "client":
        query = query.eq("client_id", current_user["id"])
    elif role == "attorney":
        query = query.eq("attorney_id", current_user["id"])
    if case_status:
        query = query.eq("status", case_status)
    if date_from:
        query = query.gte("filed_date", date_from)
    if date_to:
        query = query.lte("filed_date", date_to)

    items = query.execute().data or []

    # Enrich with client and attorney names — both are in the users table
    user_ids = set()
    for item in items:
        if item.get("client_id"):
            user_ids.add(item["client_id"])
        if item.get("attorney_id"):
            user_ids.add(item["attorney_id"])

    user_map: dict = {}
    if user_ids:
        users_res = supabase.table("users").select("id,full_name,avatar_url").in_("id", list(user_ids)).execute()
        user_map = {u["id"]: u for u in (users_res.data or [])}

    for item in items:
        client = user_map.get(item.get("client_id"))
        attorney = user_map.get(item.get("attorney_id"))
        item["client_name"] = client["full_name"] if client else None
        item["attorney_name"] = attorney["full_name"] if attorney else None
        item["hearings"] = []  # populated on detail view

    page = (skip // limit) + 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 1,
    }


@router.get("/my", response_model=List[schemas.CaseOut], summary="Get my cases")
def get_my_cases(current_user: dict = Depends(auth_utils.get_current_user)):
    role = current_user.get("role", "client")
    if role == "client":
        result = supabase.table("cases").select(_CASE_LIST_COLS).eq("client_id", current_user["id"]).order("created_at", desc=True).execute()
    elif role == "attorney":
        result = supabase.table("cases").select(_CASE_LIST_COLS).eq("attorney_id", current_user["id"]).order("created_at", desc=True).execute()
    else:
        result = supabase.table("cases").select(_CASE_LIST_COLS).order("created_at", desc=True).execute()
    return result.data or []


@router.get("/{case_id}", response_model=schemas.CaseOut, summary="Get case by ID")
def get_case(case_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("cases").select("*").eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    case = result.data[0]
    role = current_user.get("role", "client")
    if role == "client" and case.get("client_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if role == "attorney" and case.get("attorney_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return case


@router.patch("/{case_id}", response_model=schemas.CaseOut, summary="Update a case")
def update_case(
    case_id: int,
    body: schemas.CaseUpdate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Only attorneys or admins can update cases")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    for date_field in ("closed_date",):
        if date_field in update_data and update_data[date_field]:
            update_data[date_field] = str(update_data[date_field])

    result = supabase.table("cases").update(update_data).eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Sync dashboard_stats for client and attorney
    updated_case = result.data[0]
    if updated_case.get("client_id"):
        _sync_dashboard_stats(updated_case["client_id"], "client")
    if updated_case.get("attorney_id"):
        _sync_dashboard_stats(updated_case["attorney_id"], "attorney")
    
    return result.data[0]


@router.delete("/{case_id}", summary="Delete a case (admin only)")
def delete_case(case_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete cases")
    
    # Get case details before deletion to sync stats
    case_result = supabase.table("cases").select("client_id,attorney_id").eq("id", case_id).execute()
    if not case_result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    case = case_result.data[0]
    
    result = supabase.table("cases").delete().eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Sync dashboard_stats for client and attorney
    if case.get("client_id"):
        _sync_dashboard_stats(case["client_id"], "client")
    if case.get("attorney_id"):
        _sync_dashboard_stats(case["attorney_id"], "attorney")
    
    return {"message": f"Case {case_id} deleted successfully"}


# ── HEARINGS ──────────────────────────────────────────────────────────────────

def _check_case_access(case_id: int, current_user: dict):
    """Verify case exists and user has access."""
    result = supabase.table("cases").select("id,client_id,attorney_id").eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    case = result.data[0]
    role = current_user.get("role", "client")
    if role == "client" and case.get("client_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if role == "attorney" and case.get("attorney_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return case


@router.get("/{case_id}/hearings", response_model=List[schemas.HearingOut], summary="Get hearings for a case")
def get_hearings(case_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    _check_case_access(case_id, current_user)
    result = (
        supabase.table("case_hearings")
        .select("*")
        .eq("case_id", case_id)
        .order("hearing_date", desc=False)
        .execute()
    )
    return result.data or []


@router.post("/{case_id}/hearings", response_model=schemas.HearingOut, status_code=201, summary="Add a hearing to a case")
def create_hearing(
    case_id: int,
    body: schemas.HearingCreate,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")
    _check_case_access(case_id, current_user)

    data = {
        "case_id": case_id,
        "hearing_date": str(body.hearing_date),
        "hearing_time": body.hearing_time,
        "court": body.court,
        "judge": body.judge,
        "status": body.status or "scheduled",
        "notes": body.notes,
    }
    # Remove None values — let DB defaults apply
    data = {k: v for k, v in data.items() if v is not None}
    data["case_id"] = case_id  # always include

    try:
        result = supabase.table("case_hearings").insert(data).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create hearing")

    try:
        _sync_next_hearing(case_id)
    except Exception:
        pass  # Don't fail the request if sync fails

    return result.data[0]


@router.put("/{case_id}/hearings/{hearing_id}", response_model=schemas.HearingOut, summary="Update a hearing")
def update_hearing(
    case_id: int,
    hearing_id: int,
    body: schemas.HearingUpdate,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")
    _check_case_access(case_id, current_user)

    existing = supabase.table("case_hearings").select("id").eq("id", hearing_id).eq("case_id", case_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Hearing not found")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "hearing_date" in update_data:
        update_data["hearing_date"] = str(update_data["hearing_date"])

    result = supabase.table("case_hearings").update(update_data).eq("id", hearing_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update hearing")

    _sync_next_hearing(case_id)
    return result.data[0]


@router.delete("/{case_id}/hearings/{hearing_id}", summary="Delete a hearing")
def delete_hearing(
    case_id: int,
    hearing_id: int,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")
    _check_case_access(case_id, current_user)

    existing = supabase.table("case_hearings").select("id").eq("id", hearing_id).eq("case_id", case_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Hearing not found")

    supabase.table("case_hearings").delete().eq("id", hearing_id).execute()
    _sync_next_hearing(case_id)
    return {"message": f"Hearing {hearing_id} deleted"}


@router.post("/{case_id}/hearings/{hearing_id}/reschedule", response_model=schemas.HearingOut, summary="Reschedule a hearing")
def reschedule_hearing(
    case_id: int,
    hearing_id: int,
    body: schemas.HearingReschedule,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")
    _check_case_access(case_id, current_user)

    existing = supabase.table("case_hearings").select("*").eq("id", hearing_id).eq("case_id", case_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Hearing not found")

    old = existing.data[0]
    notes = f"Rescheduled from {old['hearing_date']}. {body.reason or ''}".strip()

    result = supabase.table("case_hearings").update({
        "hearing_date": str(body.new_date),
        "hearing_time": body.new_time or old.get("hearing_time"),
        "status": "scheduled",
        "notes": notes,
        "rescheduled_from_id": hearing_id,
    }).eq("id", hearing_id).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to reschedule hearing")

    _sync_next_hearing(case_id)
    return result.data[0]


def _sync_next_hearing(case_id: int):
    """Keep cases.next_hearing_date in sync with the earliest upcoming hearing.
    Wrapped in try/except — silently skips if columns don't exist in this DB version."""
    try:
        from datetime import date as date_type
        today = str(date_type.today())
        upcoming = (
            supabase.table("case_hearings")
            .select("hearing_date,hearing_time")
            .eq("case_id", case_id)
            .eq("status", "scheduled")
            .gte("hearing_date", today)
            .order("hearing_date", desc=False)
            .limit(1)
            .execute()
        )
        if upcoming.data:
            next_h = upcoming.data[0]
            supabase.table("cases").update({
                "next_hearing_date": next_h["hearing_date"],
                "next_hearing_time": next_h.get("hearing_time"),
            }).eq("id", case_id).execute()
        else:
            supabase.table("cases").update({
                "next_hearing_date": None,
                "next_hearing_time": None,
            }).eq("id", case_id).execute()
    except Exception:
        pass  # Columns may not exist in all DB versions — non-critical
