from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/cases", tags=["Cases"])

# List view excludes description — kept in detail endpoint
_CASE_LIST_COLS = "id,case_number,case_name,case_type,status,client_id,attorney_id,next_hearing_date,next_hearing_time,court,judge,filed_date,closed_date,created_at"


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
        "next_hearing_date": str(case.next_hearing_date) if case.next_hearing_date else None,
        "next_hearing_time": case.next_hearing_time,
        "court": case.court,
        "judge": case.judge,
        "filed_date": str(case.filed_date) if case.filed_date else None,
    }
    result = supabase.table("cases").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create case")
    return result.data[0]


@router.get("", response_model=schemas.PaginatedCasesOut, summary="Get all cases (admin) or my cases (client/attorney)")
def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    case_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    import math
    role = current_user.get("role", "client")
    cols = "id,case_number,case_name,case_type,status,client_id,attorney_id,next_hearing_date,next_hearing_time,court,judge,filed_date,closed_date,created_at"

    # Count query
    count_q = supabase.table("cases").select("id", count="exact")
    if role == "client":
        count_q = count_q.eq("client_id", current_user["id"])
    elif role == "attorney":
        count_q = count_q.eq("attorney_id", current_user["id"])
    if case_status:
        count_q = count_q.eq("status", case_status)
    total = count_q.execute().count or 0

    # Data query
    query = supabase.table("cases").select(_CASE_LIST_COLS).order("created_at", desc=True).range(skip, skip + limit - 1)
    if role == "client":
        query = query.eq("client_id", current_user["id"])
    elif role == "attorney":
        query = query.eq("attorney_id", current_user["id"])
    if case_status:
        query = query.eq("status", case_status)

    items = query.execute().data or []
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
    for date_field in ("next_hearing_date", "closed_date"):
        if date_field in update_data and update_data[date_field]:
            update_data[date_field] = str(update_data[date_field])

    result = supabase.table("cases").update(update_data).eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    return result.data[0]


@router.delete("/{case_id}", summary="Delete a case (admin only)")
def delete_case(case_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete cases")
    result = supabase.table("cases").delete().eq("id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"message": f"Case {case_id} deleted successfully"}
