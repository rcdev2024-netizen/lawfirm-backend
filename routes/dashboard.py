from fastapi import APIRouter, Depends
from database import supabase
import schemas
import auth as auth_utils

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
