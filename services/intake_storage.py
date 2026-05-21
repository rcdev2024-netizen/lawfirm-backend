"""Supabase Storage helpers for intake file uploads."""
import os
import uuid
from typing import Optional, Tuple

from fastapi import HTTPException

from database import get_supabase

BUCKET = os.getenv("INTAKE_STORAGE_BUCKET", "intake-uploads")
MAX_FILE_BYTES = int(os.getenv("INTAKE_MAX_FILE_MB", "10")) * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "application/pdf",
}


def _ext_from_content_type(content_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
    }
    return mapping.get(content_type, "bin")


def upload_intake_file(
    file_bytes: bytes,
    file_name: str,
    content_type: str,
    uploaded_by: int,
    draft_id: Optional[int] = None,
    category: str = "intake_form",
) -> Tuple[str, str, Optional[str]]:
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: JPG, PNG, WEBP, PDF",
        )
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum upload size")

    ext = _ext_from_content_type(content_type)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in file_name)[:120]
    storage_path = f"{uploaded_by}/{uuid.uuid4().hex}_{safe_name}.{ext}"

    sb = get_supabase()
    try:
        sb.storage.from_(BUCKET).upload(
            storage_path,
            file_bytes,
            {"content-type": content_type, "upsert": False},
        )
    except Exception as e:
        err = str(e).lower()
        if "bucket" in err or "not found" in err:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Storage bucket '{BUCKET}' not found. "
                    "Create it in Supabase Dashboard → Storage (private bucket)."
                ),
            ) from e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e

    public_url: Optional[str] = None
    try:
        signed = sb.storage.from_(BUCKET).create_signed_url(storage_path, 60 * 60 * 24 * 7)
        public_url = signed.get("signedURL") or signed.get("signedUrl")
    except Exception:
        pass

    row = sb.table("intake_uploads").insert({
        "uploaded_by": uploaded_by,
        "draft_id": draft_id,
        "file_name": file_name,
        "file_type": content_type,
        "file_size": len(file_bytes),
        "storage_path": storage_path,
        "public_url": public_url,
        "upload_category": category,
    }).execute()

    if not row.data:
        raise HTTPException(status_code=500, detail="Failed to record upload metadata")

    return storage_path, public_url or "", row.data[0]["id"]
