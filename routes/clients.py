"""
Client Management API — `clients` table is source of truth.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status

import auth as auth_utils
import schemas
from limiter import limiter
from services.client_management import (
    get_client_by_id,
    list_clients,
    patch_client,
    require_staff_role,
    search_clients,
    soft_delete_client,
    upload_client_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["Client Management"])


def require_staff(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    require_staff_role(current_user.get("role", ""))
    return current_user


def require_admin_or_attorney(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or attorney access required")
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


@router.get("/{client_id}", response_model=schemas.ClientDetailOut, summary="Client profile (with valid_ids)")
def get_client_endpoint(
    client_id: int,
    _user: dict = Depends(require_admin_or_attorney),
):
    return get_client_by_id(client_id)


@router.patch("/{client_id}", response_model=schemas.ClientDetailOut, summary="Update client")
def patch_client_endpoint(
    client_id: int,
    body: schemas.ClientManagementUpdate,
    user: dict = Depends(require_staff),
):
    updates = body.model_dump(exclude_none=True)
    if body.contact:
        updates["contact"] = body.contact.model_dump(exclude_none=True)
    if body.personal:
        updates["personal"] = body.personal.model_dump(exclude_none=True)
    if body.valid_ids:
        updates["valid_ids"] = body.valid_ids.model_dump(exclude_none=True)
    if body.profile_photo_upload_id:
        updates["profile_photo_upload_id"] = body.profile_photo_upload_id
        from services.storage_urls import extract_storage_path, resolve_upload_id_to_signed_url
        url = resolve_upload_id_to_signed_url(body.profile_photo_upload_id)
        if url:
            updates["profile_photo_url"] = extract_storage_path(url) or url
    return patch_client(client_id, updates, staff_id=user["id"])


@router.post(
    "/{client_id}/uploads",
    response_model=schemas.ClientUploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload profile or ID image for client",
)
@limiter.limit("30/minute")
async def upload_client_file_endpoint(
    request: Request,
    client_id: int,
    file: UploadFile = File(...),
    category: str = Form("profile_photo"),
    user: dict = Depends(require_staff),
):
    """
    category: profile_photo | valid_id_primary | valid_id_secondary
    (aliases: profile_photo, valid_id_primary, valid_id_secondary)
    """
    try:
        content = await file.read()
        return upload_client_file(
            client_id,
            content,
            file.filename or "upload",
            file.content_type or "application/octet-stream",
            category,
            user["id"],
            user.get("role", "attorney"),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("client upload failed client_id=%s", client_id)
        raise HTTPException(status_code=500, detail="Upload failed") from None


@router.delete("/{client_id}", summary="Archive client (soft delete)")
def delete_client_endpoint(
    client_id: int,
    _user: dict = Depends(require_staff),
):
    return soft_delete_client(client_id)


@router.patch("/{client_id}/approval", deprecated=True, include_in_schema=False)
def update_client_approval_deprecated(client_id: int):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Approval workflow removed. Clients are active when created.",
    )


@router.post("", status_code=status.HTTP_410_GONE, include_in_schema=False)
def create_client_deprecated():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use POST /api/intake/drafts/{id}/finalize to register clients.",
    )
