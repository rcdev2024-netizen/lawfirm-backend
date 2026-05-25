from fastapi import APIRouter, Depends, Query, HTTPException
from database import supabase
import schemas
import auth as auth_utils
from datetime import date
from typing import Optional
import math

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats, summary="Get dashboard stats for current user")
def get_dashboard_stats(
    user_id: Optional[int] = Query(None, description="Get stats for a specific user (admin only)"),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view stats for other users")
    uid = user_id if user_id else current_user["id"]
    role = current_user.get("role", "client")

    try:
        result = supabase.table("dashboard_stats").select(
            "active_cases,total_cases,cases_open,cases_in_progress,cases_review,cases_closed,"
            "upcoming_appointments,unpaid_invoices,total_documents,unread_messages,unread_notifications"
        ).eq("user_id", uid).execute()
        if result.data:
            row = result.data[0]
            return schemas.DashboardStats(
                active_cases=row.get("active_cases", 0),
                upcoming_appointments=row.get("upcoming_appointments", 0),
                total_documents=row.get("total_documents", 0),
                unpaid_invoices=row.get("unpaid_invoices", 0),
                unread_messages=row.get("unread_messages", 0),
                unread_notifications=row.get("unread_notifications", 0),
                total_cases=row.get("total_cases", 0),
                cases_in_progress=row.get("cases_in_progress", 0),
                cases_review=row.get("cases_review", 0),
                cases_closed=row.get("cases_closed", 0),
                cases_open=row.get("cases_open", 0),
            )
    except Exception:
        pass

    return _compute_stats_fallback(uid, role)


def _compute_stats_fallback(uid: int, role: str) -> schemas.DashboardStats:
    active_cases = upcoming_appointments = total_documents = 0
    unpaid_invoices = unread_messages = unread_notifications = 0
    total_cases = cases_in_progress = cases_review = cases_closed = cases_open = 0

    try:
        if role == "client":
            cases_res = supabase.table("cases").select("id,status").eq("client_id", uid).execute()
        elif role == "attorney":
            cases_res = supabase.table("cases").select("id,status").eq("attorney_id", uid).execute()
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
            r = supabase.table("appointments").select("id", count="exact").eq("user_id", uid).eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
            case_ids = [c["id"] for c in all_cases]
            if case_ids:
                r = supabase.table("documents").select("id", count="exact").in_("case_id", case_ids).execute()
                total_documents = r.count or 0
            r = supabase.table("invoices").select("id", count="exact").eq("client_id", uid).eq("status", "unpaid").execute()
            unpaid_invoices = r.count or 0
        elif role == "attorney":
            r = supabase.table("appointments").select("id", count="exact").eq("attorney_id", uid).eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
        else:
            r = supabase.table("appointments").select("id", count="exact").eq("status", "confirmed").gte("preferred_date", today).execute()
            upcoming_appointments = r.count or 0
            r = supabase.table("documents").select("id", count="exact").execute()
            total_documents = r.count or 0
            r = supabase.table("invoices").select("id", count="exact").eq("status", "unpaid").execute()
            unpaid_invoices = r.count or 0

        r = supabase.table("messages").select("id", count="exact").eq("recipient_id", uid).eq("is_read", False).execute()
        unread_messages = r.count or 0
        r = supabase.table("notifications").select("id", count="exact").eq("user_id", uid).eq("is_read", False).execute()
        unread_notifications = r.count or 0
    except Exception:
        pass

    return schemas.DashboardStats(
        active_cases=active_cases,
        upcoming_appointments=upcoming_appointments,
        total_documents=total_documents,
        unpaid_invoices=unpaid_invoices,
        unread_messages=unread_messages,
        unread_notifications=unread_notifications,
        total_cases=total_cases,
        cases_in_progress=cases_in_progress,
        cases_review=cases_review,
        cases_closed=cases_closed,
        cases_open=cases_open,
    )


@router.get("/today-schedule", response_model=schemas.TodayScheduleOut, summary="Get today's schedule")
def get_today_schedule(current_user: dict = Depends(auth_utils.get_current_user)):
    role = current_user.get("role", "client")
    uid = current_user["id"]
    today_str = str(date.today())

    try:
        if role == "admin":
            appt_res = (
                supabase.table("appointments")
                .select("id,full_name,email,preferred_date,preferred_time,attorney_id,user_id,status,practice_area,appointment_type")
                .eq("preferred_date", today_str)
                .order("preferred_time")
                .execute()
            )
        elif role == "attorney":
            appt_res = (
                supabase.table("appointments")
                .select("id,full_name,email,preferred_date,preferred_time,attorney_id,user_id,status,practice_area,appointment_type")
                .eq("preferred_date", today_str)
                .eq("attorney_id", uid)
                .order("preferred_time")
                .execute()
            )
        else:
            appt_res = (
                supabase.table("appointments")
                .select("id,full_name,email,preferred_date,preferred_time,attorney_id,user_id,status,practice_area,appointment_type")
                .eq("preferred_date", today_str)
                .eq("user_id", uid)
                .order("preferred_time")
                .execute()
            )

        appointments = appt_res.data or []
        attorney_ids = list({a["attorney_id"] for a in appointments if a.get("attorney_id")})
        attorney_map: dict = {}
        if attorney_ids:
            attorneys_res = supabase.table("users").select("id,full_name").in_("id", attorney_ids).execute()
            attorney_map = {u["id"]: u["full_name"] for u in (attorneys_res.data or [])}

        if role == "admin":
            grouped: dict = {}
            for appt in appointments:
                atty_id = appt.get("attorney_id")
                atty_name = attorney_map.get(atty_id, "Unassigned") if atty_id else "Unassigned"
                key = atty_id or 0
                if key not in grouped:
                    grouped[key] = {"attorney_id": atty_id, "attorney_name": atty_name, "appointments": []}
                grouped[key]["appointments"].append(appt)
            schedules = list(grouped.values())
        elif role == "attorney":
            schedules = [{"attorney_id": uid, "attorney_name": current_user.get("full_name", ""), "appointments": appointments}]
        else:
            schedules = [{"attorney_id": None, "attorney_name": "My Appointments", "appointments": appointments}]

        return schemas.TodayScheduleOut(date=today_str, schedules=schedules, total_appointments=len(appointments))
    except Exception:
        return schemas.TodayScheduleOut(date=today_str, schedules=[], total_appointments=0)


@router.get("/cases", response_model=schemas.PaginatedCasesOut, summary="Get paginated cases for dashboard (with names)")
def get_dashboard_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    status: Optional[str] = Query(None),
    hearing_date_from: Optional[str] = Query(None, description="Filter by next_hearing_date >= this date (YYYY-MM-DD)"),
    hearing_date_to: Optional[str] = Query(None, description="Filter by next_hearing_date <= this date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search by case name, case number, or case type"),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    role = current_user.get("role", "client")
    uid = current_user["id"]
    skip = (page - 1) * limit

    # ── Count query (for accurate total with filters applied) ──────────
    count_q = supabase.table("cases").select("id", count="exact")
    if role == "client":
        count_q = count_q.eq("client_id", uid)
    elif role == "attorney":
        count_q = count_q.eq("attorney_id", uid)
    if status:
        count_q = count_q.eq("status", status)
    if hearing_date_from:
        count_q = count_q.gte("next_hearing_date", hearing_date_from)
    if hearing_date_to:
        count_q = count_q.lte("next_hearing_date", hearing_date_to)
    if search:
        count_q = count_q.ilike("case_name", f"%{search}%")

    try:
        total = count_q.execute().count or 0
    except Exception:
        total = 0

    # ── Data query ─────────────────────────────────────────────────────
    data_q = (
        supabase.table("cases")
        .select(
            "id,case_number,case_name,case_type,status,client_id,attorney_id,"
            "next_hearing_date,next_hearing_time,created_at,"
            "attorney:users!cases_attorney_id_fkey(full_name),"
            "client:users!cases_client_id_fkey(full_name)"
        )
        .order("next_hearing_date", desc=False)
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )

    if role == "client":
        data_q = data_q.eq("client_id", uid)
    elif role == "attorney":
        data_q = data_q.eq("attorney_id", uid)
    if status:
        data_q = data_q.eq("status", status)
    if hearing_date_from:
        data_q = data_q.gte("next_hearing_date", hearing_date_from)
    if hearing_date_to:
        data_q = data_q.lte("next_hearing_date", hearing_date_to)
    if search:
        data_q = data_q.ilike("case_name", f"%{search}%")

    cases = data_q.execute().data or []

    # ── Flatten joined user names ──────────────────────────────────────
    enriched = []
    for c in cases:
        atty = c.pop("attorney", None)
        client = c.pop("client", None)
        enriched.append({
            **c,
            "attorney_name": atty.get("full_name") if atty else None,
            "client_name":   client.get("full_name") if client else None,
        })

    return schemas.PaginatedCasesOut(
        items=enriched, total=total, page=page, limit=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )


