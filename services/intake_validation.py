"""Step-scoped validation and 422 error formatting for client intake (3-step wizard)."""
from typing import Any, Dict, List

from fastapi import HTTPException, status

from services.intake_helpers import (
    EMAIL_RE,
    PH_PHONE_RE,
    normalize_phone,
)

# Intake wizard: personal → contact → valid_ids (cases created later in Case Management)
INTAKE_STEP_COUNT = 3
SECTIONS = ("personal", "contact", "valid_ids")
STEP_TO_SECTION = {1: "personal", 2: "contact", 3: "valid_ids"}


def _err(field: str, message: str) -> Dict[str, str]:
    return {"field": field, "message": message}


def validate_sections(raw: Dict[str, Any], sections: List[str]) -> List[Dict[str, str]]:
    """Validate only the listed draft_data sections (partial PATCH). Ignores case_info."""
    errors: List[Dict[str, str]] = []
    # case_info is not part of intake — skip if accidentally sent
    sections = [s for s in sections if s in SECTIONS]

    if "personal" in sections:
        p = raw.get("personal") or {}
        if not p:
            errors.append(_err("personal", "Personal information is required"))
        else:
            if not (p.get("first_name") or "").strip():
                errors.append(_err("personal.first_name", "First name is required"))
            if not (p.get("last_name") or "").strip():
                errors.append(_err("personal.last_name", "Last name is required"))
            if not p.get("birth_date"):
                errors.append(_err("personal.birth_date", "Birth date is required"))
            if not (p.get("nationality") or "").strip():
                errors.append(_err("personal.nationality", "Nationality is required"))

    if "contact" in sections:
        c = raw.get("contact") or {}
        if not c:
            errors.append(_err("contact", "Contact information is required"))
        else:
            email = c.get("email")
            if not email:
                errors.append(_err("contact.email", "Email is required"))
            elif not EMAIL_RE.match(str(email)):
                errors.append(_err("contact.email", "Invalid email format"))
            phone = c.get("phone_number")
            if not phone:
                errors.append(_err("contact.phone_number", "Phone number is required"))
            elif not PH_PHONE_RE.match(normalize_phone(str(phone)).replace(" ", "")):
                errors.append(
                    _err(
                        "contact.phone_number",
                        "Phone number should be a valid Philippine mobile number (09XXXXXXXXX)",
                    )
                )
            if not (c.get("address") or "").strip():
                errors.append(_err("contact.address", "Address is required"))

    if "valid_ids" in sections:
        v = raw.get("valid_ids") or {}
        if not v:
            errors.append(_err("valid_ids", "Valid ID information is required"))
        else:
            if not v.get("primary_id_type"):
                errors.append(_err("valid_ids.primary_id_type", "Primary ID type is required"))
            if not (v.get("primary_id_number") or "").strip():
                errors.append(_err("valid_ids.primary_id_number", "Primary ID number is required"))

    return errors


def validate_step_only(step: int, raw: Dict[str, Any]) -> List[Dict[str, str]]:
    """Validate a single wizard step (1–3) against merged draft_data."""
    if step < 1 or step > INTAKE_STEP_COUNT:
        return []
    section = STEP_TO_SECTION.get(step)
    if not section:
        return []
    return validate_sections(raw, [section])


def validate_all_steps(raw: Dict[str, Any]) -> List[Dict[str, str]]:
    """All steps required before finalize (no case_info)."""
    errors: List[Dict[str, str]] = []
    for step in range(1, INTAKE_STEP_COUNT + 1):
        errors.extend(validate_step_only(step, raw))
    email = (raw.get("contact") or {}).get("email")
    if not email:
        errors.append(_err("contact.email", "Email is required to create portal account"))
    return errors


def raise_validation_422(errors: List[Dict[str, str]]) -> None:
    if not errors:
        return
    detail_loc = [
        {
            "loc": ["body", "draft_data", *e["field"].split(".")],
            "msg": e["message"],
            "type": "value_error",
        }
        for e in errors
    ]
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_loc)


def validation_errors_for_response(errors: List[Dict[str, str]]) -> dict:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }
