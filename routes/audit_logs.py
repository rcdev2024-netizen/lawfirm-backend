from fastapi import APIRouter, Depends, Query
from typing import Optional
from database import supabase
import schemas
import auth as auth_utils
import math

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


def log_action(
    user_id: Optional[int],
    user_name: Optional[str],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    try:
        supabase.table("audit_logs").insert({
            "user_id": user_id,
            "user_name": user_name,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "description": description,
            "ip_address": ip_address,
        }).execute()
    except Exception:
        pass


@router.get("", response_model=schemas.PaginatedAuditLogsOut, summary="Get audit logs (admin sees all, others see own)")
def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    role = current_user.get("role", "client")
    skip = (page - 1) * limit

    count_query = supabase.table("audit_logs").select("id", count="exact")
    data_query = (
        supabase.table("audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )

    if role != "admin":
        count_query = count_query.eq("user_id", current_user["id"])
        data_query = data_query.eq("user_id", current_user["id"])

    if action:
        count_query = count_query.eq("action", action)
        data_query = data_query.eq("action", action)

    if entity_type:
        count_query = count_query.eq("entity_type", entity_type)
        data_query = data_query.eq("entity_type", entity_type)

    total = count_query.execute().count or 0
    items = data_query.execute().data or []

    return schemas.PaginatedAuditLogsOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )
