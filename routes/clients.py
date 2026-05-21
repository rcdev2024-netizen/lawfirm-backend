"""
Client Management API — `clients` table is source of truth.

Staff (admin, attorney, secretary, paralegal) list, search, edit, archive clients.
No approval workflow. Cases use user_id as client_id on /api/cases until migrated.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

import auth as auth_utils
from database import supabase
import schemas
from services.client_management import (
    get_client_by_id,
    list_clients,
    patch_client,
    require_staff_role,
    search_clients,
    soft_delete_client,
)

router = APIRouter(prefix="/api/clients", tags=["Client Management"])


def require_staff(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    require_staff_role(current_user.get("role", ""))
    return current_user


@router.get("", response_model=schemas.PaginatedClientsManagementOut, summary="List clients")
def list_clients_endpoint(
    q: Optional[str] = Query(None, description="Filter by full_name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_deleted: bool = Query(False, description="Default: active clients only"),
    _user: dict = Depends(require_staff),
):
    return list_clients(skip=skip, limit=limit, q=q, is_deleted=is_deleted)


@router.get("/search", response_model=List[schemas.ClientSearchResult], summary="Search clients")
def search_clients_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    _user: dict = Depends(require_staff),
):
    return search_clients(q, limit=limit)


@router.get("/{client_id}", response_model=schemas.ClientDetailOut, summary="Client profile")
def get_client_endpoint(
    client_id: int,
    _user: dict = Depends(require_staff),
):
    return get_client_by_id(client_id)


@router.patch("/{client_id}", response_model=schemas.ClientDetailOut, summary="Update client")
def patch_client_endpoint(
    client_id: int,
    body: schemas.ClientManagementUpdate,
    _user: dict = Depends(require_staff),
):
    updates = body.model_dump(exclude_none=True)
    if body.contact:
        updates["contact"] = body.contact.model_dump(exclude_none=True)
    return patch_client(client_id, updates)


@router.delete("/{client_id}", summary="Archive client (soft delete)")
def delete_client_endpoint(
    client_id: int,
    _user: dict = Depends(require_staff),
):
    return soft_delete_client(client_id)


# ── Deprecated ────────────────────────────────────────────────

@router.patch("/{client_id}/approval", deprecated=True, include_in_schema=False)
def update_client_approval_deprecated(client_id: int):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Approval workflow removed. Clients are active when created.",
    )


# Legacy path used user_id — redirect staff to new id-based routes
@router.post("", status_code=status.HTTP_410_GONE, include_in_schema=False)
def create_client_deprecated():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use POST /api/intake/drafts/{id}/finalize to register clients.",
    )
