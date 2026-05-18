from fastapi import APIRouter, Depends, Query
from database import supabase
import schemas
import auth as auth_utils
from datetime import date
import math

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats, summary="Get dashboard stats for current user")
def get_dashboard_stats(current_user: dict = Depends(auth_utils.get_current_user)):
    uid = current_user["id"]
    role = current_user.get("role", "client")

    active_cases = 0
    upcoming_appointments = 0
    total_documents = 0
    unpaid_invoices = 0
    unread_messages = 0
    unread_notifications = 0

    try:
        if role == "client":
            cases_res = supabase.table("cases").select("id", count="exact").eq("client_id", uid).in_("status", ["open", "in_progress", "review"]).execute()
            active_cases = cases_res.count or 0

            appt_res = supabase.table("appointments").select("id", count="exact").eq("user_id", uid).eq("status", "confirmed").execute()
            upcoming_appointments = appt_res.count or 0

            case_ids_res = supabase.table("cases").select("id").eq("client_id", uid).execute()
            case_ids = [c["id"] for c in (case_ids_res.data or [])]
            if case_ids:
                docs_res = supabase.table("documents").select("id", count="exact").in_("case_id", case_ids).execute()
                total_documents = docs_res.count or 0

            inv_res = supabase.table("invoices").select("id", count="exact").eq("client_id", uid).eq("status", "unpaid").execute()
            unpaid_invoices = inv_res.count or 0

        elif role == "attorney":
            cases_res = supabase.table("cases").select("id", count="exact").eq("attorney_id", uid).in_("status", ["open", "in_progress", "review"]).execute()
            active_cases = cases_res.count or 0

            appt_res = supabase.table("appointments").select("id", count="exact").eq("attorney_id", uid).eq("status", "confirmed").execute()
            upcoming_appointments = appt_res.count or 0

        else:
            cases_res = supabase.table("cases").select("id", count="exact").in_("status", ["open", "in_progress", "review"]).execute()
            active_cases = cases_res.count or 0

            appt_res = supabase.table("appointments").select("id", count="exact").eq("status", "confirmed").execute()
            upcoming_appointments = appt_res.count or 0

            docs_res = supabase.table("documents").select("id", count="exact").execute()
            total_documents = docs_res.count or 0

            inv_res = supabase.table("invoices").select("id", count="exact").eq("status", "unpaid").execute()
            unpaid_invoices = inv_res.count or 0

        msg_res = supabase.table("messages").select("id", count="exact").eq("recipient_id", uid).eq("is_read", False).execute()
        unread_messages = msg_res.count or 0

        notif_res = supabase.table("notifications").select("id", count="exact").eq("user_id", uid).eq("is_read", False).execute()
        unread_notifications = notif_res.count or 0

    except Exception:
        pass

    return schemas.DashboardStats(
        active_cases=active_cases,
        upcoming_appointments=upcoming_appointments,
        total_documents=total_documents,
        unpaid_invoices=unpaid_invoices,
        unread_messages=unread_messages,
        unread_notifications=unread_notifications,
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
                .select("*")
                .eq("preferred_date", today_str)
                .order("preferred_time")
                .execute()
            )
        elif role == "attorney":
            appt_res = (
                supabase.table("appointments")
                .select("*")
                .eq("preferred_date", today_str)
                .eq("attorney_id", uid)
                .order("preferred_time")
                .execute()
            )
        else:
            appt_res = (
                supabase.table("appointments")
                .select("*")
                .eq("preferred_date", today_str)
                .eq("user_id", uid)
                .order("preferred_time")
                .execute()
            )

        appointments = appt_res.data or []

        attorney_ids = list({a["attorney_id"] for a in appointments if a.get("attorney_id")})
        attorney_map: dict = {}
        if attorney_ids:
            attorneys_res = supabase.table("users").select("id, full_name").in_("id", attorney_ids).execute()
            attorney_map = {u["id"]: u["full_name"] for u in (attorneys_res.data or [])}

        if role in ("admin",):
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
            schedules = [{
                "attorney_id": uid,
                "attorney_name": current_user.get("full_name", ""),
                "appointments": appointments,
            }]
        else:
            schedules = [{
                "attorney_id": None,
                "attorney_name": "My Appointments",
                "appointments": appointments,
            }]

        return schemas.TodayScheduleOut(
            date=today_str,
            schedules=schedules,
            total_appointments=len(appointments),
        )
    except Exception as e:
        return schemas.TodayScheduleOut(date=today_str, schedules=[], total_appointments=0)


@router.get("/cases", response_model=schemas.PaginatedCasesOut, summary="Get paginated cases for dashboard (with names)")
def get_dashboard_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    role = current_user.get("role", "client")
    uid = current_user["id"]
    skip = (page - 1) * limit

    count_q = supabase.table("cases").select("id", count="exact")
    data_q = supabase.table("cases").select("*").order("created_at", desc=True).range(skip, skip + limit - 1)

    if role == "client":
        count_q = count_q.eq("client_id", uid)
        data_q = data_q.eq("client_id", uid)
    elif role == "attorney":
        count_q = count_q.eq("attorney_id", uid)
        data_q = data_q.eq("attorney_id", uid)

    if status:
        count_q = count_q.eq("status", status)
        data_q = data_q.eq("status", status)

    total = count_q.execute().count or 0
    cases = data_q.execute().data or []

    user_ids = set()
    for c in cases:
        if c.get("attorney_id"):
            user_ids.add(c["attorney_id"])
        if c.get("client_id"):
            user_ids.add(c["client_id"])

    user_map: dict = {}
    if user_ids:
        users_res = supabase.table("users").select("id, full_name").in_("id", list(user_ids)).execute()
        user_map = {u["id"]: u["full_name"] for u in (users_res.data or [])}

    enriched = []
    for c in cases:
        enriched.append({
            **c,
            "attorney_name": user_map.get(c.get("attorney_id"), "") if c.get("attorney_id") else None,
            "client_name": user_map.get(c.get("client_id"), "") if c.get("client_id") else None,
        })

    return schemas.PaginatedCasesOut(
        items=enriched,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )
