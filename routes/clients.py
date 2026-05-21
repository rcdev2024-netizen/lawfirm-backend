from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/clients", tags=["Clients"])


def require_admin_or_attorney(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or attorney access required")
    return current_user


def require_admin(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _get_client_role_id() -> int:
    result = supabase.table("roles").select("id").eq("name", "client").execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Client role not found")
    return result.data[0]["id"]


@router.get("", response_model=schemas.PaginatedClientsOut, summary="List all clients (admin/attorney)")
def list_clients(
    approval_status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: dict = Depends(require_admin_or_attorney)
):
    import math
    client_role_id = _get_client_role_id()

    # Count query
    count_q = supabase.table("users").select("id", count="exact").eq("role_id", client_role_id)
    if approval_status:
        count_q = count_q.eq("approval_status", approval_status)
    if q:
        count_q = count_q.ilike("full_name", f"%{q}%")
    total = count_q.execute().count or 0

    # Data query
    query = (
        supabase.table("users")
        .select("id, full_name, email, phone, is_active, approval_status, created_at")
        .eq("role_id", client_role_id)
        .order("created_at", desc=True)
    )
    if approval_status:
        query = query.eq("approval_status", approval_status)
    if q:
        query = query.ilike("full_name", f"%{q}%")
    items = query.range(skip, skip + limit - 1).execute().data or []
    page = (skip // limit) + 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 1,
    }


@router.get("/search", response_model=List[schemas.UserSearchResult], summary="Search clients by name/email")
def search_clients(
    q: str = Query(..., min_length=1),
    _user: dict = Depends(require_admin_or_attorney)
):
    client_role_id = _get_client_role_id()
    result = (
        supabase.table("users")
        .select("id, full_name, email, phone")
        .eq("role_id", client_role_id)
        .eq("approval_status", "approved")
        .ilike("full_name", f"%{q}%")
        .limit(10)
        .execute()
    )
    return result.data or []


@router.post("", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED, summary="Add a client (admin)")
def create_client(payload: schemas.ClientCreate, admin: dict = Depends(require_admin)):
    existing = supabase.table("users").select("id").eq("email", payload.email).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_id = _get_client_role_id()
    hashed_pw = auth_utils.get_password_hash(payload.password)

    result = supabase.table("users").insert({
        "full_name": payload.full_name,
        "email": payload.email,
        "hashed_password": hashed_pw,
        "phone": payload.phone,
        "role_id": role_id,
        "is_active": True,
        "approval_status": "approved"
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create client")
    return result.data[0]


@router.patch("/{user_id}", response_model=schemas.ClientOut, summary="Update client info (admin)")
def update_client(user_id: int, payload: schemas.ClientUpdate, admin: dict = Depends(require_admin)):
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        result = supabase.table("users").select("id,full_name,email,phone,is_active,approval_status,created_at").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Client not found")
        return result.data[0]

    result = supabase.table("users").update(update_data).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return result.data[0]


@router.patch("/{user_id}/approval", response_model=schemas.ClientOut, summary="Approve or reject a client (admin)")
def update_client_approval(user_id: int, payload: schemas.ClientApprovalUpdate, admin: dict = Depends(require_admin)):
    if payload.approval_status not in ("approved", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="approval_status must be approved, rejected, or pending")

    result = supabase.table("users").update({"approval_status": payload.approval_status}).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return result.data[0]


@router.delete("/{user_id}", summary="Delete a client (admin)")
def delete_client(user_id: int, admin: dict = Depends(require_admin)):
    result = supabase.table("users").delete().eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": f"Client {user_id} deleted successfully"}
