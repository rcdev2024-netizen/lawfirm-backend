from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/attorneys", tags=["Attorneys"])


def require_admin(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_admin_or_attorney(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or attorney access required")
    return current_user


def _get_attorney_role_id() -> int:
    result = supabase.table("roles").select("id").eq("name", "attorney").execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Attorney role not found")
    return result.data[0]["id"]


@router.get("", response_model=List[schemas.AttorneyOut], summary="List all attorneys (admin/attorney)")
def list_attorneys(
    q: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: dict = Depends(require_admin_or_attorney)
):
    attorney_role_id = _get_attorney_role_id()
    query = (
        supabase.table("users")
        .select("id, full_name, email, phone, specialization, is_active, created_at")
        .eq("role_id", attorney_role_id)
        .order("full_name")
    )
    if q:
        query = query.ilike("full_name", f"%{q}%")
    result = query.range(skip, skip + limit - 1).execute()
    return result.data or []


@router.get("/search", response_model=List[schemas.UserSearchResult], summary="Search attorneys by name")
def search_attorneys(
    q: str = Query(..., min_length=1),
    _user: dict = Depends(require_admin_or_attorney)
):
    attorney_role_id = _get_attorney_role_id()
    result = (
        supabase.table("users")
        .select("id, full_name, email, phone")
        .eq("role_id", attorney_role_id)
        .eq("is_active", True)
        .ilike("full_name", f"%{q}%")
        .limit(10)
        .execute()
    )
    return result.data or []


@router.post("", response_model=schemas.AttorneyOut, status_code=status.HTTP_201_CREATED, summary="Add an attorney (admin)")
def create_attorney(payload: schemas.AttorneyCreate, admin: dict = Depends(require_admin)):
    existing = supabase.table("users").select("id").eq("email", payload.email).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_id = _get_attorney_role_id()
    hashed_pw = auth_utils.get_password_hash(payload.password)

    result = supabase.table("users").insert({
        "full_name": payload.full_name,
        "email": payload.email,
        "hashed_password": hashed_pw,
        "phone": payload.phone,
        "specialization": payload.specialization,
        "role_id": role_id,
        "is_active": True,
        "approval_status": "approved"
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create attorney")
    return result.data[0]


@router.patch("/{user_id}", response_model=schemas.AttorneyOut, summary="Update attorney (admin)")
def update_attorney(user_id: int, payload: schemas.AttorneyUpdate, admin: dict = Depends(require_admin)):
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        result = supabase.table("users").select("id,full_name,email,phone,specialization,is_active,created_at").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Attorney not found")
        return result.data[0]

    result = supabase.table("users").update(update_data).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Attorney not found")
    return result.data[0]


@router.delete("/{user_id}", summary="Delete an attorney (admin)")
def delete_attorney(user_id: int, admin: dict = Depends(require_admin)):
    result = supabase.table("users").delete().eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Attorney not found")
    return {"message": f"Attorney {user_id} deleted successfully"}
