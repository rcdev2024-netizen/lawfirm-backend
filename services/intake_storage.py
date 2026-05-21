"""Supabase Storage helpers for intake file uploads."""
import logging
import os
import re
import uuid
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status

from database import get_supabase

logger = logging.getLogger(__name__)

BUCKET = os.getenv("INTAKE_STORAGE_BUCKET", "intake-uploads")
MAX_FILE_BYTES = int(os.getenv("INTAKE_MAX_FILE_MB", "10")) * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}

ALLOWED_UPLOAD_CATEGORIES = {
    "intake_form",
    "valid_id_primary",
    "valid_id_secondary",
    "profile_photo",
    "other",
    "ocr_document",
}

EXT_TO_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def normalize_upload_category(category: str) -> str:
    """Normalize FE aliases; reject unknown categories with 400."""
    raw = (category or "intake_form").strip().lower().replace("-", "_")
    aliases = {
        "ocr": "ocr_document",
        "form": "intake_form",
        "id_primary": "valid_id_primary",
        "id_secondary": "valid_id_secondary",
        "photo": "profile_photo",
    }
    normalized = aliases.get(raw, raw)
    if normalized not in ALLOWED_UPLOAD_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid upload category",
                "errors": [
                    f"category must be one of: {', '.join(sorted(ALLOWED_UPLOAD_CATEGORIES))}"
                ],
            },
        )
    return normalized


def resolve_content_type(content_type: str, file_name: str) -> str:
    """Infer MIME from extension when browser sends application/octet-stream."""
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in ALLOWED_CONTENT_TYPES:
        return "image/jpeg" if ct == "image/jpg" else ct
    ext = os.path.splitext(file_name or "")[1].lower()
    inferred = EXT_TO_CONTENT_TYPE.get(ext)
    if inferred:
        return inferred
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "message": "Unsupported file type",
            "errors": ["Allowed: JPG, PNG, WEBP, PDF"],
        },
    )


def validate_intake_draft(draft_id: int, user_id: int, role: str) -> dict:
    """Ensure draft exists and caller may attach uploads to it."""
    sb = get_supabase()
    row = sb.table("client_intake_drafts").select("id, created_by, status").eq("id", draft_id).execute()
    if not row.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    draft = row.data[0]
    if draft.get("status") == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload to a finalized draft",
        )
    if draft.get("created_by") != user_id and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Draft does not belong to this user",
        )
    return draft


def _ext_from_content_type(content_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
    }
    return mapping.get(content_type, "bin")


def _storage_error_detail(exc: Exception) -> Tuple[int, str]:
    msg = str(exc).lower()
    if "bucket" in msg and ("not found" in msg or "does not exist" in msg):
        return (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Storage bucket '{BUCKET}' not found. Create a private bucket in Supabase Storage.",
        )
    if "duplicate" in msg or "already exists" in msg:
        return status.HTTP_409_CONFLICT, "File already exists at this path; retry upload."
    if "payload too large" in msg or "too large" in msg:
        return status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds storage or platform size limit."
    if "401" in msg or "unauthorized" in msg or "invalid api key" in msg:
        return status.HTTP_503_SERVICE_UNAVAILABLE, "Storage authentication failed. Check SUPABASE_SERVICE_KEY."
    return status.HTTP_500_INTERNAL_SERVER_ERROR, "Storage upload failed"


def _db_error_detail(exc: Exception) -> Tuple[int, Dict[str, Any]]:
    msg = str(exc)
    lower = msg.lower()
    if "chk_upload_category" in lower or "upload_category" in lower:
        return status.HTTP_400_BAD_REQUEST, {
            "message": "Invalid upload category for database",
            "errors": [
                "Run migration_client_intake_upload_fix.sql to allow ocr_document, "
                f"or use one of: {', '.join(sorted(ALLOWED_UPLOAD_CATEGORIES))}",
            ],
        }
    if "violates foreign key" in lower and "draft_id" in lower:
        return status.HTTP_400_BAD_REQUEST, {
            "message": "Invalid draft_id",
            "errors": ["draft_id does not exist"],
        }
    return status.HTTP_500_INTERNAL_SERVER_ERROR, {
        "message": "Failed to save upload metadata",
        "errors": [msg[:200]],
    }


def upload_intake_file(
    file_bytes: bytes,
    file_name: str,
    content_type: str,
    uploaded_by: int,
    draft_id: Optional[int] = None,
    category: str = "intake_form",
    user_role: str = "attorney",
) -> Tuple[str, str, int]:
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Empty file", "errors": ["file must not be empty"]},
        )

    normalized_category = normalize_upload_category(category)
    resolved_type = resolve_content_type(content_type, file_name)

    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "File too large",
                "errors": [f"Maximum size is {MAX_FILE_BYTES // (1024 * 1024)} MB"],
            },
        )

    if draft_id is not None:
        validate_intake_draft(draft_id, uploaded_by, user_role)

    ext = _ext_from_content_type(resolved_type)
    base = os.path.splitext(file_name or "upload")[0]
    safe_name = re.sub(r"[^\w.\-]", "_", base)[:120] or "upload"
    storage_path = f"{uploaded_by}/{uuid.uuid4().hex}_{safe_name}.{ext}"

    sb = get_supabase()
    try:
        sb.storage.from_(BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": resolved_type,
                "upsert": "false",
                "cache-control": "3600",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Supabase storage upload failed path=%s bucket=%s", storage_path, BUCKET)
        code, detail = _storage_error_detail(e)
        raise HTTPException(status_code=code, detail=detail) from e

    public_url: Optional[str] = None
    try:
        signed = sb.storage.from_(BUCKET).create_signed_url(storage_path, 60 * 60 * 24 * 7)
        if isinstance(signed, dict):
            public_url = signed.get("signedURL") or signed.get("signedUrl")
        elif hasattr(signed, "data") and signed.data:
            public_url = signed.data.get("signedUrl") or signed.data.get("signedURL")
    except Exception:
        logger.warning("Could not create signed URL for %s", storage_path, exc_info=True)

    try:
        row = sb.table("intake_uploads").insert({
            "uploaded_by": uploaded_by,
            "draft_id": draft_id,
            "file_name": file_name or safe_name,
            "file_type": resolved_type,
            "file_size": len(file_bytes),
            "storage_path": storage_path,
            "public_url": public_url,
            "upload_category": normalized_category,
        }).execute()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("intake_uploads insert failed draft_id=%s", draft_id)
        code, detail = _db_error_detail(e)
        # Best-effort cleanup of orphaned storage object
        try:
            sb.storage.from_(BUCKET).remove([storage_path])
        except Exception:
            pass
        raise HTTPException(status_code=code, detail=detail) from e

    if not row.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record upload metadata",
        )

    return storage_path, public_url or "", row.data[0]["id"]
