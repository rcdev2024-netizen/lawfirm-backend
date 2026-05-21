"""Signed URL helpers for private intake-uploads bucket."""
import logging
import os
import re
from typing import Optional

from database import get_supabase

logger = logging.getLogger(__name__)

BUCKET = os.getenv("INTAKE_STORAGE_BUCKET", "intake-uploads")
SIGNED_URL_TTL = int(os.getenv("INTAKE_SIGNED_URL_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days


def extract_storage_path(reference: Optional[str]) -> Optional[str]:
    """
    Normalize a stored value to a storage object path.
    Accepts raw path or a Supabase storage/signed URL.
    """
    if not reference or not str(reference).strip():
        return None
    ref = str(reference).strip()
    if not ref.startswith("http"):
        return ref.lstrip("/")

    patterns = [
        rf"/object/sign/{re.escape(BUCKET)}/",
        rf"/object/public/{re.escape(BUCKET)}/",
        rf"/storage/v1/object/sign/{re.escape(BUCKET)}/",
        rf"{re.escape(BUCKET)}/",
    ]
    for pat in patterns:
        if pat in ref:
            path = ref.split(pat, 1)[1].split("?")[0]
            return path.lstrip("/")
    return None


def create_signed_url(storage_path: str, expires_in: Optional[int] = None) -> Optional[str]:
    if not storage_path:
        return None
    ttl = expires_in or SIGNED_URL_TTL
    try:
        sb = get_supabase()
        signed = sb.storage.from_(BUCKET).create_signed_url(storage_path, ttl)
        if isinstance(signed, dict):
            return signed.get("signedURL") or signed.get("signedUrl")
        if hasattr(signed, "data") and signed.data:
            return signed.data.get("signedUrl") or signed.data.get("signedURL")
    except Exception:
        logger.warning("Failed to sign path=%s", storage_path, exc_info=True)
    return None


def resolve_signed_url(reference: Optional[str]) -> Optional[str]:
    """Return a fresh signed HTTPS URL for a path or prior URL."""
    path = extract_storage_path(reference)
    if not path:
        return reference if reference and str(reference).startswith("http") else None
    signed = create_signed_url(path)
    return signed or reference


def resolve_upload_id_to_signed_url(upload_id: int) -> Optional[str]:
    row = (
        get_supabase()
        .table("intake_uploads")
        .select("storage_path, public_url")
        .eq("id", upload_id)
        .execute()
    )
    if not row.data:
        return None
    u = row.data[0]
    path = u.get("storage_path") or extract_storage_path(u.get("public_url"))
    if path:
        return create_signed_url(path)
    return u.get("public_url")
