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

ID_TYPES = [
    "Passport", "Driver's License", "PhilSys ID", "UMID", "PRC ID",
    "Postal ID", "Voter's ID", "Senior Citizen ID", "Company ID",
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


def validate_step(step: int, raw: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    data = parse_draft_data(raw)

    if step >= 1:
        if not data.personal:
            errors.append("Step 1: personal information is required")
        else:
            p = data.personal
            if not p.first_name:
                errors.append("firstName is required")
            if not p.last_name:
                errors.append("lastName is required")
            if not p.birth_date:
                errors.append("birthDate is required")
            if not p.nationality:
                errors.append("nationality is required")

    if step >= 2:
        if not data.contact:
            errors.append("Step 2: contact information is required")
        else:
            c = data.contact
            if not EMAIL_RE.match(str(c.email)):
                errors.append("Invalid email format")
            if not c.phone_number:
                errors.append("phoneNumber is required")
            elif not PH_PHONE_RE.match(normalize_phone(c.phone_number).replace(" ", "")):
                errors.append("phoneNumber should be a valid Philippine mobile number")
            if not c.address:
                errors.append("address is required")

    if step >= 3:
        if not data.valid_ids:
            errors.append("Step 3: valid ID information is required")
        else:
            v = data.valid_ids
            if not v.primary_id_type:
                errors.append("primaryIdType is required")
            if not v.primary_id_number:
                errors.append("primaryIdNumber is required")

    if step >= 4:
        if not data.case_info:
            errors.append("Step 4: case information is required")
        elif not data.case_info.case_type:
            errors.append("caseType is required")

    return errors


def validate_finalize(raw: Dict[str, Any]) -> None:
    errors = validate_step(4, raw)
    if not raw.get("contact", {}).get("email"):
        errors.append("email is required to create portal account")
    if errors:
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": errors})


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
        if overwrite or section not in result:
            result[section] = incoming[section]
        else:
            base = dict(result.get(section) or {})
            for k, v in (incoming[section] or {}).items():
                if v is not None and (overwrite or not base.get(k)):
                    base[k] = v
            result[section] = base
    return result
