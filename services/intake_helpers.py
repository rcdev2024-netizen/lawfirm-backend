"""Shared helpers for client intake validation and name building."""
import re
import secrets
import string
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from schemas_intake import (
    IntakeDraftData,
    PersonalInfoStep,
    ContactInfoStep,
    ValidIdsStep,
    CaseInfoStep,
)


PH_PHONE_RE = re.compile(r"^(\+63|0)?9\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Legacy flat list — prefer GET /api/intake/id-types (valid_id_types table)
ID_TYPES = [
    "Philippine Passport",
    "PhilSys National ID",
    "Driver's License",
    "UMID (Unified Multi-Purpose ID)",
    "PRC ID",
    "Postal ID",
    "Voter's ID",
    "SSS ID",
    "GSIS eCard",
    "Senior Citizen ID",
    "PWD ID",
    "OWWA ID",
    "OFW ID",
    "TIN ID",
    "Barangay ID",
    "Company ID",
    "School ID",
    "Police Clearance",
    "NBI Clearance",
    "Birth Certificate",
    "Marriage Certificate",
]

CASE_CATEGORIES = [
    "Family Law", "Criminal Law", "Civil Law", "Labor Law",
    "Corporate Law", "Immigration", "Real Estate", "Other",
]


def build_full_name(
    first: str,
    middle: Optional[str],
    last: str,
    suffix: Optional[str] = None,
) -> str:
    parts = [first.strip()]
    if middle and middle.strip():
        parts.append(middle.strip())
    parts.append(last.strip())
    name = " ".join(parts)
    if suffix and suffix.strip():
        name = f"{name} {suffix.strip()}"
    return name


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("63") and len(digits) == 12:
        return f"0{digits[2:]}"
    if len(digits) == 10 and digits.startswith("9"):
        return f"0{digits}"
    return phone.strip()


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def draft_data_to_dict(data: Optional[IntakeDraftData]) -> Dict[str, Any]:
    if not data:
        return {}
    out: Dict[str, Any] = {}
    if data.personal:
        out["personal"] = data.personal.model_dump(mode="json")
    if data.contact:
        out["contact"] = data.contact.model_dump(mode="json")
    if data.valid_ids:
        out["valid_ids"] = data.valid_ids.model_dump(mode="json")
    if data.case_info:
        out["case_info"] = data.case_info.model_dump(mode="json")
    if data.password:
        out["password"] = data.password
    return out


def parse_draft_data(raw: Dict[str, Any]) -> IntakeDraftData:
    personal = contact = valid_ids = case_info = None
    try:
        if raw.get("personal"):
            personal = PersonalInfoStep(**raw["personal"])
    except Exception:
        pass
    try:
        if raw.get("contact"):
            contact = ContactInfoStep(**raw["contact"])
    except Exception:
        pass
    try:
        if raw.get("valid_ids"):
            valid_ids = ValidIdsStep(**raw["valid_ids"])
    except Exception:
        pass
    try:
        if raw.get("case_info"):
            case_info = CaseInfoStep(**raw["case_info"])
    except Exception:
        pass
    return IntakeDraftData(
        personal=personal,
        contact=contact,
        valid_ids=valid_ids,
        case_info=case_info,
        password=raw.get("password"),
    )


def merge_raw_draft_payload(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Merge partial PATCH body (only sections present in incoming)."""
    return merge_draft_data(existing or {}, incoming or {}, overwrite=False)


def resolve_upload_public_url(upload_id: int) -> Optional[str]:
    from database import get_supabase

    row = (
        get_supabase()
        .table("intake_uploads")
        .select("public_url, storage_path")
        .eq("id", upload_id)
        .execute()
    )
    if not row.data:
        return None
    u = row.data[0]
    if u.get("public_url"):
        return u["public_url"]
    return u.get("storage_path")


def resolve_valid_ids_uploads(valid_ids: Dict[str, Any]) -> Dict[str, Any]:
    """Map FE upload IDs to URLs for finalize."""
    out = dict(valid_ids or {})
    pairs = (
        ("profile_photo_upload_id", "profile_photo_url"),
        ("primary_id_image_upload_id", "primary_id_image_url"),
        ("secondary_id_image_upload_id", "secondary_id_image_url"),
    )
    for upload_key, url_key in pairs:
        uid = out.get(upload_key)
        if uid and not out.get(url_key):
            try:
                url = resolve_upload_public_url(int(uid))
                if url:
                    out[url_key] = url
            except (TypeError, ValueError):
                pass
    return out


def validate_finalize(raw: Dict[str, Any]) -> None:
    from services.intake_validation import raise_validation_422, validate_all_steps

    errors = validate_all_steps(raw)
    if errors:
        raise_validation_422(errors)


def extraction_to_draft_fields(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Map flat OCR keys into wizard draft_data structure."""
    personal: Dict[str, Any] = {}
    contact: Dict[str, Any] = {}
    case_info: Dict[str, Any] = {}

    key_map_personal = {
        "firstName": "first_name", "first_name": "first_name",
        "middleName": "middle_name", "middle_name": "middle_name",
        "lastName": "last_name", "last_name": "last_name",
        "suffix": "suffix", "gender": "gender",
        "birthDate": "birth_date", "birth_date": "birth_date",
        "civilStatus": "civil_status", "civil_status": "civil_status",
        "nationality": "nationality",
        "placeOfBirth": "place_of_birth", "place_of_birth": "place_of_birth",
        "occupation": "occupation",
    }
    key_map_contact = {
        "email": "email",
        "phoneNumber": "phone_number", "phone_number": "phone_number",
        "alternatePhone": "alternate_phone", "alternate_phone": "alternate_phone",
        "address": "address", "barangay": "barangay", "city": "city",
        "province": "province", "zipCode": "zip_code", "zip_code": "zip_code",
        "country": "country",
    }
    key_map_case = {
        "caseType": "case_type", "case_type": "case_type",
        "caseCategory": "case_category", "case_category": "case_category",
        "notes": "notes", "referredBy": "referred_by", "referred_by": "referred_by",
    }

    for src, dest in key_map_personal.items():
        if src in extracted and extracted[src]:
            personal[dest] = extracted[src]
    for src, dest in key_map_contact.items():
        if src in extracted and extracted[src]:
            contact[dest] = extracted[src]
    for src, dest in key_map_case.items():
        if src in extracted and extracted[src]:
            case_info[dest] = extracted[src]

    if personal.get("first_name") and personal.get("last_name"):
        personal["full_name"] = build_full_name(
            personal.get("first_name", ""),
            personal.get("middle_name"),
            personal.get("last_name", ""),
            personal.get("suffix"),
        )

    out: Dict[str, Any] = {}
    if personal:
        out["personal"] = personal
    if contact:
        out["contact"] = contact
    if case_info:
        out["case_info"] = case_info
    return out


def merge_draft_data(
    existing: Dict[str, Any],
    incoming: Dict[str, Any],
    overwrite: bool = False,
) -> Dict[str, Any]:
    result = dict(existing or {})
    for section in ("personal", "contact", "valid_ids", "case_info"):
        if section not in incoming:
            continue
        incoming_section = incoming[section] or {}
        if overwrite or section not in result:
            result[section] = dict(incoming_section)
        else:
            base = dict(result.get(section) or {})
            for k, v in incoming_section.items():
                if v is not None and (overwrite or v != "" or k not in base):
                    base[k] = v
            result[section] = base
    if incoming.get("password"):
        result["password"] = incoming["password"]
    # Auto full_name when personal names change
    p = result.get("personal") or {}
    if p.get("first_name") and p.get("last_name"):
        p["full_name"] = build_full_name(
            p.get("first_name", ""),
            p.get("middle_name"),
            p.get("last_name", ""),
            p.get("suffix"),
        )
        result["personal"] = p
    return result
