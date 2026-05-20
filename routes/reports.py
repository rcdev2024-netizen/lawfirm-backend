from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Any, Dict
from database import supabase
import auth as auth_utils
from datetime import date, timedelta
import re

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# ── Natural Language Query Parser ────────────────────────────────────────────
# Parses free-text queries into structured filter objects.
# No external AI API needed — rule-based matching on known entities.

def parse_query(query: str) -> Dict[str, Any]:
    """
    Parse a natural language query into structured filters.
    Returns: { entity, filters, sort, limit, summary }
    """
    q = query.lower().strip()
    result: Dict[str, Any] = {
        "entity": None,
        "filters": {},
        "sort": "created_at",
        "sort_desc": True,
        "limit": 100,
        "raw_query": query
    }

    # ── Detect entity ─────────────────────────────────────────────────────────
    if any(w in q for w in ["case", "cases", "lawsuit", "litigation", "hearing"]):
        result["entity"] = "cases"
    elif any(w in q for w in ["appointment", "appointments", "booking", "schedule", "consultation"]):
        result["entity"] = "appointments"
    elif any(w in q for w in ["invoice", "invoices", "billing", "payment", "unpaid", "paid", "overdue"]):
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
        result["entity"] = "cases"  # default

    # ── Date ranges ───────────────────────────────────────────────────────────
    today = date.today()

    if "today" in q:
        result["filters"]["date_from"] = str(today)
        result["filters"]["date_to"] = str(today)
    elif "yesterday" in q:
        yesterday = today - timedelta(days=1)
        result["filters"]["date_from"] = str(yesterday)
        result["filters"]["date_to"] = str(yesterday)
    elif "this week" in q or "current week" in q:
        start = today - timedelta(days=today.weekday())
        result["filters"]["date_from"] = str(start)
        result["filters"]["date_to"] = str(today)
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

    # Specific month names
    months = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
              "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
    for month_name, month_num in months.items():
        if month_name in q:
            year = today.year
            # Check for year mention
            year_match = re.search(r'\b(20\d{2})\b', q)
            if year_match:
                year = int(year_match.group(1))
            import calendar
            last_day = calendar.monthrange(year, month_num)[1]
            result["filters"]["date_from"] = f"{year}-{month_num:02d}-01"
            result["filters"]["date_to"] = f"{year}-{month_num:02d}-{last_day}"
            break

    # ── Status filters ────────────────────────────────────────────────────────
    # Cases
    if result["entity"] == "cases":
        if any(w in q for w in ["open cases", "open"]) and "closed" not in q:
            result["filters"]["status"] = "open"
        elif any(w in q for w in ["closed cases", "closed"]):
            result["filters"]["status"] = "closed"
        elif any(w in q for w in ["in progress", "in-progress", "ongoing", "active"]):
            result["filters"]["status"] = "in_progress"
        elif any(w in q for w in ["under review", "review"]):
            result["filters"]["status"] = "review"

    # Appointments
    if result["entity"] == "appointments":
        if "pending" in q:
            result["filters"]["status"] = "pending"
        elif "confirmed" in q:
            result["filters"]["status"] = "confirmed"
        elif "cancelled" in q or "canceled" in q:
            result["filters"]["status"] = "cancelled"
        elif "completed" in q:
            result["filters"]["status"] = "completed"
        elif "rescheduled" in q:
            result["filters"]["status"] = "rescheduled"
        elif "expired" in q:
            result["filters"]["status"] = "expired"

    # Invoices
    if result["entity"] == "invoices":
        if "unpaid" in q:
            result["filters"]["status"] = "unpaid"
        elif "paid" in q and "unpaid" not in q:
            result["filters"]["status"] = "paid"
        elif "overdue" in q:
            result["filters"]["status"] = "overdue"

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
    if any(w in q for w in ["oldest", "earliest", "first"]):
        result["sort_desc"] = False
    if "hearing" in q and result["entity"] == "cases":
        result["sort"] = "next_hearing_date"
    if "date" in q and result["entity"] == "appointments":
        result["sort"] = "preferred_date"

    # ── Limit ─────────────────────────────────────────────────────────────────
    limit_match = re.search(r'\b(top|first|last)\s+(\d+)\b', q)
    if limit_match:
        result["limit"] = min(int(limit_match.group(2)), 200)

    return result


def execute_report(parsed: Dict[str, Any], role: str, uid: int) -> Dict[str, Any]:
    """Execute the parsed query against Supabase and return results + metadata."""
    entity = parsed["entity"]
    filters = parsed["filters"]
    limit = parsed.get("limit", 100)
    sort = parsed.get("sort", "created_at")
    sort_desc = parsed.get("sort_desc", True)

    rows = []
    columns = []
    total = 0

    try:
        if entity == "cases":
            q = supabase.table("cases").select(
                "id,case_number,case_name,case_type,status,court,judge,"
                "next_hearing_date,next_hearing_time,filed_date,created_at,updated_at,"
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
            if filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order(sort, desc=sort_desc).limit(limit)
            data = q.execute().data or []
            # Flatten joins
            rows = [{
                **{k: v for k, v in r.items() if k not in ("attorney", "client")},
                "attorney_name": (r.get("attorney") or {}).get("full_name", "—"),
                "client_name":   (r.get("client")   or {}).get("full_name", "—"),
            } for r in data]
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
            if filters.get("date_from"):
                q = q.gte("created_at", filters["date_from"])
            if filters.get("date_to"):
                q = q.lte("created_at", filters["date_to"] + "T23:59:59")
            q = q.order("created_at", desc=sort_desc).limit(limit)
            rows = q.execute().data or []
            columns = ["invoice_number","status","amount","tax","total","due_date","paid_date","created_at"]

        elif entity == "clients":
            if role not in ("admin", "attorney"):
                raise HTTPException(status_code=403, detail="Access denied")
            q = supabase.table("users").select("id,full_name,email,phone,is_active,approval_status,created_at").eq("role", "client")
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

        total = len(rows)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    return {
        "entity": entity,
        "columns": columns,
        "rows": rows,
        "total": total,
        "filters_applied": filters,
        "parsed_query": parsed["raw_query"]
    }


@router.post("/query", summary="Natural language report query")
def run_report_query(
    body: dict,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    query = (body.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    role = current_user.get("role", "client")
    uid = current_user["id"]

    parsed = parse_query(query)
    result = execute_report(parsed, role, uid)
    return result


@router.get("/suggestions", summary="Get example report queries")
def get_suggestions(current_user: dict = Depends(auth_utils.get_current_user)):
    role = current_user.get("role", "client")
    base = [
        "Show all cases this month",
        "Show open cases",
        "Show closed cases this year",
        "Show pending appointments",
        "Show confirmed appointments this week",
        "Show unpaid invoices",
    ]
    admin_extra = [
        "Show all criminal cases",
        "Show cases assigned to Atty. Holt",
        "Show all clients registered this month",
        "Show overdue invoices",
        "Show rescheduled appointments",
        "Show audit logs today",
        "Show top 10 cases by hearing date",
        "Show in progress cases this year",
        "Show all attorneys",
        "Show expired appointments",
    ]
    return {"suggestions": base + (admin_extra if role == "admin" else [])}
