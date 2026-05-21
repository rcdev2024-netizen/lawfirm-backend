from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Any, Dict
from database import supabase
import auth as auth_utils
from datetime import date, timedelta
import re
import calendar as cal_module
from main import limiter
from fastapi import Request

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# ── Natural Language Query Parser ─────────────────────────────────────────────

def parse_query(query: str) -> Dict[str, Any]:
    q = query.lower().strip()
    result: Dict[str, Any] = {
        "entity": None, "filters": {}, "sort": "created_at",
        "sort_desc": True, "limit": 100, "raw_query": query
    }

    # ── Entity detection ──────────────────────────────────────────────────────
    if any(w in q for w in ["case", "cases", "lawsuit", "litigation", "hearing", "hearings"]):
        result["entity"] = "cases"
    elif any(w in q for w in ["appointment", "appointments", "booking", "schedule", "consultation"]):
        result["entity"] = "appointments"
    elif any(w in q for w in ["invoice", "invoices", "billing", "payment", "unpaid", "paid", "overdue", "revenue", "balance"]):
        result["entity"] = "invoices"
    elif any(w in q for w in ["client", "clients"]):
        result["entity"] = "clients"
    elif any(w in q for w in ["attorney", "attorneys", "lawyer", "lawyers", "atty"]):
        result["entity"] = "attorneys"
    elif any(w in q for w in ["document", "documents", "file", "files"]):
        result["entity"] = "documents"
    elif any(w in q for w in ["audit", "log", "logs", "activity", "activities"]):
        result["entity"] = "audit_logs"
    else:
        result["entity"] = "cases"

    today = date.today()

    # ── Date ranges ───────────────────────────────────────────────────────────
    if "today" in q:
        result["filters"]["date_from"] = str(today)
        result["filters"]["date_to"] = str(today)
    elif "tomorrow" in q:
        tomorrow = today + timedelta(days=1)
        result["filters"]["date_from"] = str(tomorrow)
        result["filters"]["date_to"] = str(tomorrow)
    elif "yesterday" in q:
        yesterday = today - timedelta(days=1)
        result["filters"]["date_from"] = str(yesterday)
        result["filters"]["date_to"] = str(yesterday)
    elif "this week" in q or "current week" in q:
        start = today - timedelta(days=today.weekday())
        result["filters"]["date_from"] = str(start)
        result["filters"]["date_to"] = str(today)
    elif "next week" in q:
        start = today + timedelta(days=7 - today.weekday())
        end = start + timedelta(days=6)
        result["filters"]["date_from"] = str(start)
        result["filters"]["date_to"] = str(end)
    elif "last week" in q:
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        result["filters"]["date_from"] = str(start)
        result["filters"]["date_to"] = str(end)
    elif "this month" in q or "current month" in q:
        result["filters"]["date_from"] = str(today.replace(day=1))
        result["filters"]["date_to"] = str(today)
    elif "last month" in q:
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        result["filters"]["date_from"] = str(last_prev.replace(day=1))
        result["filters"]["date_to"] = str(last_prev)
    elif "this year" in q or "current year" in q:
        result["filters"]["date_from"] = str(today.replace(month=1, day=1))
        result["filters"]["date_to"] = str(today)
    elif "last year" in q:
        result["filters"]["date_from"] = f"{today.year - 1}-01-01"
        result["filters"]["date_to"] = f"{today.year - 1}-12-31"
    elif "recent" in q or "recently" in q:
        result["filters"]["date_from"] = str(today - timedelta(days=30))
        result["filters"]["date_to"] = str(today)

    # Specific month names
    months = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
              "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
    for month_name, month_num in months.items():
        if month_name in q:
            year = today.year
            year_match = re.search(r'\b(20\d{2})\b', q)
            if year_match:
                year = int(year_match.group(1))
            last_day = cal_module.monthrange(year, month_num)[1]
            result["filters"]["date_from"] = f"{year}-{month_num:02d}-01"
            result["filters"]["date_to"] = f"{year}-{month_num:02d}-{last_day}"
            break

    # ── Due date filter (invoices) ────────────────────────────────────────────
    if result["entity"] == "invoices" and "due" in q:
        result["filters"]["use_due_date"] = True
        if "today" in q:
            result["filters"]["due_date_from"] = str(today)
            result["filters"]["due_date_to"] = str(today)
        elif "this week" in q:
            start = today - timedelta(days=today.weekday())
            result["filters"]["due_date_from"] = str(start)
            result["filters"]["due_date_to"] = str(start + timedelta(days=6))
        elif "30 days" in q or "30-day" in q:
            result["filters"]["due_date_to"] = str(today - timedelta(days=30))
        elif "90 days" in q or "90-day" in q:
            result["filters"]["due_date_to"] = str(today - timedelta(days=90))

    # ── Hearing date filter (cases) ───────────────────────────────────────────
    if result["entity"] == "cases" and ("hearing" in q):
        result["filters"]["use_hearing_date"] = True
        if "today" in q:
            result["filters"]["hearing_date_from"] = str(today)
            result["filters"]["hearing_date_to"] = str(today)
        elif "this week" in q:
            start = today - timedelta(days=today.weekday())
            result["filters"]["hearing_date_from"] = str(start)
            result["filters"]["hearing_date_to"] = str(start + timedelta(days=6))
        elif "this month" in q:
            result["filters"]["hearing_date_from"] = str(today.replace(day=1))
            last_day = cal_module.monthrange(today.year, today.month)[1]
            result["filters"]["hearing_date_to"] = f"{today.year}-{today.month:02d}-{last_day}"
        result["sort"] = "next_hearing_date"
        result["sort_desc"] = False

    # ── Status filters ────────────────────────────────────────────────────────
    if result["entity"] == "cases":
        if "open" in q and "closed" not in q:
            result["filters"]["status"] = "open"
        elif "closed" in q:
            result["filters"]["status"] = "closed"
        elif any(w in q for w in ["in progress", "in-progress", "ongoing", "active"]):
            result["filters"]["status"] = "in_progress"
        elif any(w in q for w in ["under review", "review"]):
            result["filters"]["status"] = "review"

        # Cases without attorney
        if any(w in q for w in ["without attorney", "unassigned", "no attorney"]):
            result["filters"]["no_attorney"] = True

        # Cases without hearing
        if any(w in q for w in ["without hearing", "no hearing", "awaiting hearing"]):
            result["filters"]["no_hearing"] = True

    if result["entity"] == "appointments":
        if "pending" in q:
            result["filters"]["status"] = "pending"
        elif "confirmed" in q:
            result["filters"]["status"] = "confirmed"
        elif any(w in q for w in ["cancelled", "canceled"]):
            result["filters"]["status"] = "cancelled"
        elif "completed" in q:
            result["filters"]["status"] = "completed"
        elif "rescheduled" in q:
            result["filters"]["status"] = "rescheduled"
        elif "expired" in q:
            result["filters"]["status"] = "expired"
        elif any(w in q for w in ["missed", "no-show"]):
            result["filters"]["status"] = "expired"

    if result["entity"] == "invoices":
        if "unpaid" in q:
            result["filters"]["status"] = "unpaid"
        elif "paid" in q and "unpaid" not in q:
            result["filters"]["status"] = "paid"
        elif "overdue" in q:
            result["filters"]["status"] = "overdue"

    # ── Client active/inactive ────────────────────────────────────────────────
    if result["entity"] == "clients":
        if any(w in q for w in ["inactive", "deactivated", "disabled"]):
            result["filters"]["is_active"] = False
        elif any(w in q for w in ["active", "enabled"]):
            result["filters"]["is_active"] = True
        if any(w in q for w in ["new", "newly", "registered", "recent"]) and "date_from" not in result["filters"]:
            result["filters"]["date_from"] = str(today - timedelta(days=30))
            result["filters"]["date_to"] = str(today)

    # ── Attorney active/inactive ──────────────────────────────────────────────
    if result["entity"] == "attorneys":
        if any(w in q for w in ["inactive", "deactivated"]):
            result["filters"]["is_active"] = False
        elif "active" in q:
            result["filters"]["is_active"] = True

    # ── Case type ─────────────────────────────────────────────────────────────
    case_types = ["criminal", "civil", "family", "immigration", "corporate",
                  "real estate", "labor", "tax", "intellectual property"]
    for ct in case_types:
        if ct in q:
            result["filters"]["case_type"] = ct.title()
            break

    # ── Practice area (appointments) ──────────────────────────────────────────
    practice_areas = ["civil litigation", "criminal defense", "family law",
                      "corporate law", "real estate", "immigration", "labor law",
                      "general consultation"]
    for pa in practice_areas:
        if pa in q:
            result["filters"]["practice_area"] = pa.title()
            break

    # ── Attorney name ─────────────────────────────────────────────────────────
    atty_match = re.search(r'(?:atty\.?|attorney|lawyer)\s+([a-z]+(?:\s+[a-z]+)?)', q)
    if atty_match:
        result["filters"]["attorney_name"] = atty_match.group(1).title()

    # ── Sorting ───────────────────────────────────────────────────────────────
    if any(w in q for w in ["oldest", "earliest", "first", "oldest open"]):
        result["sort_desc"] = False
    if any(w in q for w in ["newest", "latest", "recent", "recently"]):
        result["sort_desc"] = True
    if "hearing" in q and result["entity"] == "cases" and "use_hearing_date" not in result["filters"]:
        result["sort"] = "next_hearing_date"
        result["sort_desc"] = False
    if "due" in q and result["entity"] == "invoices":
        result["sort"] = "due_date"

    # ── Limit ─────────────────────────────────────────────────────────────────
    limit_match = re.search(r'\b(?:top|first|last)\s+(\d+)\b', q)
    if limit_match:
        result["limit"] = min(int(limit_match.group(1)), 200)

    return result


def execute_report(parsed: Dict[str, Any], role: str, uid: int) -> Dict[str, Any]:
    entity = parsed["entity"]
    filters = parsed["filters"]
    limit = parsed.get("limit", 100)
    sort = parsed.get("sort", "created_at")
    sort_desc = parsed.get("sort_desc", True)
    rows = []
    columns = []

    try:
        if entity == "cases":
            q = supabase.table("cases").select(
                "id,case_number,case_name,case_type,status,court,judge,"
                "next_hearing_date,next_hearing_time,filed_date,created_at,"
                "attorney:users!cases_attorney_id_fkey(full_name),"
                "client:users!cases_client_id_fkey(full_name)"
            )
            if role == "client":
                q = q.eq("client_id", uid)
            elif role == "attorney":
                q = q.eq("attorney_id", uid)
            if filters.get("status"):
                q = q.eq("status", filters["status"])
            if filters.get("case_type"):
                q = q.ilike("case_type", f"%{filters['case_type']}%")
            if filters.get("attorney_name"):
                # Filter by attorney name via subquery not supported in supabase-py directly
                # We'll filter post-fetch
                pass
            if filters.get("no_attorney"):
                q = q.is_("attorney_id", "null")
            if filters.get("no_hearing"):
                q = q.is_("next_hearing_date", "null")
            # Hearing date filter
            if filters.get("use_hearing_date"):
                if filters.get("hearing_date_from"):
                    q = q.gte("next_hearing_date", filters["hearing_date_from"])
                if filters.get("hearing_date_to"):
                    q = q.lte("next_hearing_date", filters["hearing_date_to"])
            elif filters.get("date_from") and not filters.get("use_hearing_date"):
                q = q.gte("created_at", filters["date_from"])
                if filters.get("date_to"):
                    q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order(sort, desc=sort_desc).limit(limit)
            data = q.execute().data or []
            rows = [{
                **{k: v for k, v in r.items() if k not in ("attorney", "client")},
                "attorney_name": (r.get("attorney") or {}).get("full_name", "—"),
                "client_name":   (r.get("client")   or {}).get("full_name", "—"),
            } for r in data]
            # Post-filter by attorney name if needed
            if filters.get("attorney_name"):
                name = filters["attorney_name"].lower()
                rows = [r for r in rows if name in (r.get("attorney_name") or "").lower()]
            columns = ["case_number","case_name","case_type","status","attorney_name",
                       "client_name","court","next_hearing_date","filed_date","created_at"]

        elif entity == "appointments":
            q = supabase.table("appointments").select("*")
            if role == "client":
                q = q.eq("user_id", uid)
            elif role == "attorney":
                q = q.eq("attorney_id", uid)
            if filters.get("status"):
                q = q.eq("status", filters["status"])
            if filters.get("practice_area"):
                q = q.ilike("practice_area", f"%{filters['practice_area']}%")
            if filters.get("date_from"):
                q = q.gte("preferred_date", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("preferred_date", filters["date_to"])
            q = q.order("preferred_date", desc=sort_desc).limit(limit)
            rows = q.execute().data or []
            columns = ["id","full_name","email","practice_area","status",
                       "preferred_date","preferred_time","appointment_type","created_at"]

        elif entity == "invoices":
            if role == "client":
                q = supabase.table("invoices").select("*").eq("client_id", uid)
            else:
                q = supabase.table("invoices").select("*")
            if filters.get("status"):
                q = q.eq("status", filters["status"])
            if filters.get("use_due_date"):
                if filters.get("due_date_from"):
                    q = q.gte("due_date", filters["due_date_from"])
                if filters.get("due_date_to"):
                    q = q.lte("due_date", filters["due_date_to"])
            elif filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
                if filters.get("date_to"):
                    q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order(sort, desc=sort_desc).limit(limit)
            rows = q.execute().data or []
            columns = ["invoice_number","status","amount","tax","total","due_date","paid_date","created_at"]

        elif entity == "clients":
            if role not in ("admin", "attorney"):
                raise HTTPException(status_code=403, detail="Access denied")
            q = supabase.table("users").select("id,full_name,email,phone,is_active,approval_status,created_at").eq("role", "client")
            if "is_active" in filters:
                q = q.eq("is_active", filters["is_active"])
            if filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order("created_at", desc=sort_desc).limit(limit)
            rows = q.execute().data or []
            columns = ["full_name","email","phone","is_active","approval_status","created_at"]

        elif entity == "attorneys":
            if role not in ("admin",):
                raise HTTPException(status_code=403, detail="Access denied")
            q = supabase.table("users").select("id,full_name,email,phone,specialization,is_active,created_at").eq("role", "attorney")
            if "is_active" in filters:
                q = q.eq("is_active", filters["is_active"])
            if filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order("created_at", desc=sort_desc).limit(limit)
            rows = q.execute().data or []
            columns = ["full_name","email","phone","specialization","is_active","created_at"]

        elif entity == "audit_logs":
            if role != "admin":
                raise HTTPException(status_code=403, detail="Access denied")
            q = supabase.table("audit_logs").select("*")
            if filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order("created_at", desc=True).limit(limit)
            rows = q.execute().data or []
            columns = ["user_name","action","entity_type","entity_id","description","ip_address","created_at"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    return {
        "entity": entity, "columns": columns, "rows": rows,
        "total": len(rows), "filters_applied": {k: v for k, v in filters.items() if not k.startswith("use_") and not k.startswith("hearing_date") and not k.startswith("due_date")},
        "parsed_query": parsed["raw_query"]
    }


@router.post("/query", summary="Natural language report query")
@limiter.limit("20/minute")
def run_report_query(request: Request, body: dict, current_user: dict = Depends(auth_utils.get_current_user)):
    query = (body.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    role = current_user.get("role", "client")
    uid = current_user["id"]
    parsed = parse_query(query)
    return execute_report(parsed, role, uid)


@router.get("/suggestions", summary="Get example report queries")
def get_suggestions(current_user: dict = Depends(auth_utils.get_current_user)):
    role = current_user.get("role", "client")

    base = [
        "Show all cases this month", "Show open cases", "Show closed cases this year",
        "Show pending appointments", "Show confirmed appointments this week",
        "Show unpaid invoices", "Show my cases", "Show cases this year",
        "Show my appointments", "Show my invoices", "Show active cases",
        "Show upcoming appointments", "Show overdue invoices",
        "Show recently created cases", "Show completed appointments",
        "Show cancelled appointments", "Show appointments today",
        "Show appointments this month", "Show paid invoices",
        "Show unpaid invoices this month", "Show cases with hearings this month",
        "Show my open cases", "Show my closed cases", "Show my pending appointments",
    ]

    attorney_extra = [
        "Show all criminal cases", "Show in progress cases", "Show cases under review",
        "Show confirmed appointments this month", "Show rescheduled appointments",
        "Show top 10 cases by hearing date", "Show cases with hearing this month",
        "List all clients", "Show recently updated cases",
        "Show cases assigned to me", "Show cases without hearings",
        "Show clients with active cases", "Show newly registered clients",
        "Show inactive clients", "Show today's appointments",
        "Show tomorrow's appointments", "Show appointments this week",
        "Show missed appointments", "Show completed appointments this month",
        "Show invoices due this week", "Show paid invoices this month",
        "Show unpaid invoices this year", "Show overdue invoices",
        "Show total cases this year", "Show top 5 active cases",
    ]

    admin_extra = [
        "Show all criminal cases", "Show cases assigned to Atty. Holt",
        "List all clients", "Show inactive clients",
        "Show active clients registered this month",
        "Show all clients registered this year", "Show overdue invoices",
        "Show rescheduled appointments", "Show audit logs today",
        "Show top 10 cases by hearing date", "Show in progress cases this year",
        "List all attorneys", "Show expired appointments",
        "Show cancelled appointments this month", "Show civil cases this year",
        "Show family law cases", "Show cases with hearing this week",
        "Show completed appointments", "Show paid invoices this month",
        "Show unpaid invoices this year", "Show audit logs this week",
        "Show cases created this month", "Show closed cases last month",
        "Show all pending appointments", "Show top 20 clients",
        "Show all active cases", "Show cases without assigned attorneys",
        "Show cases awaiting hearing", "Show recently updated cases",
        "Show oldest open cases", "Show newest cases",
        "Show cases filed this week", "Show active attorneys",
        "Show inactive attorneys", "Show newly registered clients",
        "Show clients without cases", "Show appointments today",
        "Show appointments tomorrow", "Show appointments this week",
        "Show missed appointments", "Show hearings scheduled today",
        "Show hearings this month", "Show cancelled hearings",
        "Show invoices due today", "Show invoices due this week",
        "Show invoices over 90 days overdue", "Show recent audit logs",
        "Show user activity today", "Show system activity this week",
        "Show total cases this month", "Show total appointments this year",
    ]

    if role == "admin":
        return {"suggestions": base + admin_extra}
    elif role == "attorney":
        return {"suggestions": base + attorney_extra}
    return {"suggestions": base}
