"""OCR extraction and field mapping for client intake forms."""
import base64
import json
import os
import re
from typing import Any, Dict, List, Tuple

import requests

from database import get_supabase
from services.intake_helpers import extraction_to_draft_fields

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_OCR_MODEL", "gpt-4o-mini")

FIELD_KEYS = [
    "firstName", "middleName", "lastName", "suffix", "gender", "birthDate",
    "civilStatus", "nationality", "placeOfBirth", "occupation",
    "email", "phoneNumber", "alternatePhone", "address", "barangay",
    "city", "province", "zipCode", "country",
    "caseType", "caseCategory", "notes", "referredBy",
]

FIELD_LABELS = {
    "firstName": "First Name",
    "middleName": "Middle Name",
    "lastName": "Last Name",
    "suffix": "Suffix",
    "gender": "Gender",
    "birthDate": "Birth Date",
    "civilStatus": "Civil Status",
    "nationality": "Nationality",
    "placeOfBirth": "Place of Birth",
    "occupation": "Occupation",
    "email": "Email",
    "phoneNumber": "Phone Number",
    "alternatePhone": "Alternate Phone",
    "address": "Address",
    "barangay": "Barangay",
    "city": "City",
    "province": "Province",
    "zipCode": "ZIP Code",
    "country": "Country",
    "caseType": "Case Type",
    "caseCategory": "Case Category",
    "notes": "Notes",
    "referredBy": "Referred By",
}

EXTRACTION_PROMPT = """You are extracting data from a Philippine law firm CLIENT REGISTRATION FORM.
Return ONLY valid JSON with this structure:
{
  "extracted_fields": { "firstName": "...", ... },
  "field_confidence": { "firstName": 0.95, ... },
  "raw_text": "full OCR text"
}
Use camelCase keys from: firstName, middleName, lastName, suffix, gender, birthDate (YYYY-MM-DD),
civilStatus, nationality, email, phoneNumber, address, barangay, city, province, zipCode,
caseType, caseCategory, notes.
Confidence is 0.0-1.0. Use low confidence (<0.6) for unclear handwriting.
If a field is missing, omit it. Never invent data."""


def _confidence_level(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


# ── Label → camelCase field mapping ──────────────────────────────────────────
# Covers all labels that appear on Philippine law firm intake forms
_LABEL_MAP: Dict[str, str] = {
    "LAST NAME":                   "lastName",
    "FIRST NAME":                  "firstName",
    "MIDDLE NAME":                 "middleName",
    "SUFFIX":                      "suffix",
    "DATE OF BIRTH":               "birthDate",
    "BIRTH DATE":                  "birthDate",
    "GENDER":                      "gender",
    "SEX":                         "gender",
    "CIVIL STATUS":                "civilStatus",
    "MARITAL STATUS":              "civilStatus",
    "NATIONALITY":                 "nationality",
    "CITIZENSHIP":                 "nationality",
    "PLACE OF BIRTH":              "placeOfBirth",
    "OCCUPATION":                  "occupation",
    "PROFESSION":                  "occupation",
    "EMAIL ADDRESS":               "email",
    "EMAIL":                       "email",
    "PHONE NUMBER":                "phoneNumber",
    "CONTACT NUMBER":              "phoneNumber",
    "MOBILE NUMBER":               "phoneNumber",
    "TELEPHONE":                   "phoneNumber",
    "ALTERNATE PHONE":             "alternatePhone",
    "ALTERNATE CONTACT":           "alternatePhone",
    "HOME ADDRESS":                "address",
    "ADDRESS":                     "address",
    "STREET ADDRESS":              "address",
    "BARANGAY":                    "barangay",
    "BRGY":                        "barangay",
    "CITY / MUNICIPALITY":         "city",
    "CITY":                        "city",
    "MUNICIPALITY":                "city",
    "PROVINCE":                    "province",
    "ZIP CODE":                    "zipCode",
    "POSTAL CODE":                 "zipCode",
    "COUNTRY":                     "country",
    "TYPE OF LEGAL CONCERN":       "caseType",
    "LEGAL CONCERN":               "caseType",
    "CASE TYPE":                   "caseType",
    "PRIORITY LEVEL":              "priorityLevel",
    "REFERRED BY":                 "referredBy",
    "NOTES / BRIEF DESCRIPTION":   "notes",
    "NOTES":                       "notes",
    "BRIEF DESCRIPTION":           "notes",
    "DESCRIPTION":                 "notes",
}

# Fields that can appear multiple on the same header line (positional split)
_POSITIONAL_GROUPS = [
    ["lastName", "firstName", "middleName", "suffix"],
    ["birthDate", "gender", "civilStatus", "nationality"],
    ["email", "phoneNumber", "alternatePhone"],
    ["city", "province", "zipCode", "country"],
]


def _is_header_line(line: str) -> bool:
    """A header line is ALL CAPS (allowing spaces, slashes, punctuation) with no digits."""
    stripped = line.strip()
    if not stripped:
        return False
    # Must be mostly uppercase letters
    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return upper_ratio >= 0.85 and len(stripped) >= 3


def _normalize_label(label: str) -> str:
    """Normalize a label token for lookup."""
    return re.sub(r"\s+", " ", label.strip().upper())


def _parse_header_line(line: str) -> List[str]:
    """
    Split a header line like 'LAST NAME FIRST NAME MIDDLE NAME SUFFIX'
    into individual label tokens using the known label map.
    Returns list of matched label strings in left-to-right order.
    """
    normalized = _normalize_label(line)
    found: List[tuple] = []  # (start_pos, end_pos, label_key)

    # Try to match known labels by scanning the normalized line
    for label in sorted(_LABEL_MAP.keys(), key=len, reverse=True):
        start = 0
        while True:
            idx = normalized.find(label, start)
            if idx == -1:
                break
            # Make sure it's not overlapping with already found labels
            overlap = any(s <= idx < e or s < idx + len(label) <= e for s, e, _ in found)
            if not overlap:
                found.append((idx, idx + len(label), label))
            start = idx + 1

    found.sort(key=lambda x: x[0])
    return [f[2] for f in found]


# How many tokens each field typically consumes in a multi-column value line
_FIELD_TOKEN_BUDGET: Dict[str, int] = {
    "birthDate":      3,   # "March 15, 1985" = 3 tokens
    "gender":         1,
    "civilStatus":    1,
    "nationality":    1,
    "lastName":       1,   # Note: compound surnames handled by OpenAI fallback
    "firstName":      1,
    "middleName":     1,
    "suffix":         1,
    "email":          1,
    "phoneNumber":    1,
    "alternatePhone": 1,
    "city":           2,   # "Legazpi City", "San Pablo City" = 2 tokens
    "province":       1,
    "zipCode":        1,
    "country":        1,
}


def _split_value_line(value_line: str, labels: List[str]) -> Dict[str, str]:
    """
    Split a value line positionally using per-field token budgets.
    Multi-space split is tried first (printed/typed column-aligned forms).
    Falls back to token-budget split for Tesseract single-space output.
    """
    result: Dict[str, str] = {}
    if not labels or not value_line.strip():
        return result

    # Try multi-space split first
    parts = re.split(r"\s{2,}", value_line.strip())
    if len(parts) >= len(labels):
        for i, label in enumerate(labels):
            field = _LABEL_MAP.get(label)
            if field and i < len(parts) and parts[i].strip():
                result[field] = parts[i].strip()
        return result

    # Single label — whole line is the value
    if len(labels) == 1:
        field = _LABEL_MAP.get(labels[0])
        if field:
            result[field] = value_line.strip()
        return result

    # Token-budget split
    tokens = value_line.strip().split()
    if not tokens:
        return result

    idx = 0
    for i, label in enumerate(labels):
        field = _LABEL_MAP.get(label)
        if not field or idx >= len(tokens):
            continue
        is_last = (i == len(labels) - 1)
        if is_last:
            chunk = tokens[idx:]
        else:
            budget = _FIELD_TOKEN_BUDGET.get(field, 1)
            chunk = tokens[idx: idx + budget]
        if chunk:
            result[field] = " ".join(chunk)
        idx += len(chunk)

    return result


def _parse_birth_date(raw: str) -> str:
    """Normalize birth date to YYYY-MM-DD."""
    raw = raw.strip()
    # Already ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw
    # Month name formats: March 15, 1985 / 15 March 1985
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", raw)
    if m:
        mon, day, year = m.groups()
        mn = months.get(mon.lower())
        if mn:
            return f"{year}-{mn:02d}-{int(day):02d}"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m:
        day, mon, year = m.groups()
        mn = months.get(mon.lower())
        if mn:
            return f"{year}-{mn:02d}-{int(day):02d}"
    # Numeric: MM/DD/YYYY or DD/MM/YYYY
    m = re.match(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", raw)
    if m:
        a, b, y = m.groups()
        y = y if len(y) == 4 else (f"19{y}" if int(y) > 30 else f"20{y}")
        return f"{y}-{int(a):02d}-{int(b):02d}"
    return raw


def _form_aware_extract(raw_text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Primary extractor for structured Philippine intake forms.
    Treats ALL CAPS lines as headers and the line immediately after as values.
    Handles multi-label header lines with positional value splitting.
    """
    fields: Dict[str, Any] = {}
    confidence: Dict[str, float] = {}

    lines = [l.rstrip() for l in raw_text.splitlines()]
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if _is_header_line(line):
            labels = _parse_header_line(line)
            if not labels:
                i += 1
                continue

            # Collect value lines (skip blank, stop at next header)
            value_lines = []
            j = i + 1
            while j < len(lines):
                vl = lines[j]
                if not vl.strip():
                    j += 1
                    continue
                if _is_header_line(vl):
                    break
                value_lines.append(vl)
                j += 1
                # Only take first non-blank value line for positional split
                if len(labels) > 1:
                    break

            if value_lines:
                value_line = value_lines[0]
                if len(labels) == 1:
                    field = _LABEL_MAP.get(labels[0])
                    if field and value_line.strip():
                        val = value_line.strip()
                        if field == "birthDate":
                            val = _parse_birth_date(val)
                        fields[field] = val
                        confidence[field] = 0.88
                else:
                    mapped = _split_value_line(value_line, labels)
                    for field, val in mapped.items():
                        if val and field not in fields:
                            if field == "birthDate":
                                val = _parse_birth_date(val)
                            fields[field] = val
                            confidence[field] = 0.85

            i = j
        else:
            i += 1

    return fields, confidence


def _heuristic_extract(raw_text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Two-pass extractor:
    1. Form-aware parser (handles structured ALL CAPS label/value forms)
    2. Regex fallback for any fields not yet found
    """
    # Pass 1: structured form parser
    fields, confidence = _form_aware_extract(raw_text)

    # Pass 2: regex fallback for fields still missing
    if "email" not in fields:
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", raw_text)
        if m:
            fields["email"] = m.group(0)
            confidence["email"] = 0.9

    if "phoneNumber" not in fields:
        m = re.search(r"(?:\+63|0)9\d{2}[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
        if m:
            fields["phoneNumber"] = m.group(0)
            confidence["phoneNumber"] = 0.75

    if "birthDate" not in fields:
        m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", raw_text)
        if m:
            d, mo, y = m.groups()
            y = y if len(y) == 4 else f"19{y}" if int(y) > 30 else f"20{y}"
            fields["birthDate"] = f"{y}-{int(mo):02d}-{int(d):02d}"
            confidence["birthDate"] = 0.5

    if "caseType" not in fields:
        m = re.search(
            r"\b(family|criminal|civil|labor|corporate|immigration|annulment|divorce)\b",
            raw_text, re.I,
        )
        if m:
            fields["caseType"] = m.group(1).title()
            confidence["caseType"] = 0.6

    return fields, confidence


def _openai_vision_extract(file_bytes: bytes, content_type: str) -> Tuple[Dict[str, Any], Dict[str, float], str]:
    b64 = base64.standard_b64encode(file_bytes).decode("ascii")
    media = "image/jpeg" if "jpeg" in content_type or "jpg" in content_type else content_type

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all client registration fields from this document."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media};base64,{b64}"},
                    },
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error: {resp.status_code} {resp.text[:300]}")

    content = resp.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    fields = parsed.get("extracted_fields") or parsed
    conf = parsed.get("field_confidence") or {k: 0.8 for k in fields}
    raw = parsed.get("raw_text") or content
    return fields, conf, raw


def process_upload_ocr(upload_id: int, draft_id: int | None, performed_by: int) -> dict:
    sb = get_supabase()
    upload = sb.table("intake_uploads").select("*").eq("id", upload_id).execute()
    if not upload.data:
        raise ValueError("Upload not found")

    u = upload.data[0]
    path = u["storage_path"]
    bucket = os.getenv("INTAKE_STORAGE_BUCKET", "intake-uploads")

    try:
        file_bytes = sb.storage.from_(bucket).download(path)
    except Exception as e:
        raise RuntimeError(f"Could not download file: {e}") from e

    content_type = u.get("file_type") or "image/jpeg"
    provider = "heuristic"
    status = "requires_review"
    error_message = None
    raw_text = ""
    extracted: Dict[str, Any] = {}
    confidence: Dict[str, float] = {}

    try:
        if OPENAI_API_KEY and content_type.startswith("image/"):
            extracted, confidence, raw_text = _openai_vision_extract(file_bytes, content_type)
            provider = "openai_vision"
            status = "completed"
        elif content_type == "application/pdf":
            status = "requires_review"
            error_message = (
                "PDF OCR requires OPENAI_API_KEY or manual entry. "
                "Upload a photo (JPG/PNG) or paste extracted text via /ocr/map-from-text."
            )
        else:
            status = "requires_review"
            error_message = (
                "Set OPENAI_API_KEY for AI OCR, or use /ocr/map-from-text with manual text."
            )
    except Exception as e:
        status = "failed"
        error_message = str(e)

    mapped = extraction_to_draft_fields(extracted)

    # Return result dict without inserting — caller manages the DB row
    result = {
        "upload_id": upload_id,
        "draft_id": draft_id,
        "status": status,
        "raw_text": raw_text,
        "extracted_fields": extracted,
        "field_confidence": confidence,
        "mapped_fields": mapped,
        "provider": provider,
        "error_message": error_message,
    }

    sb.table("intake_ai_logs").insert({
        "draft_id": draft_id,
        "action": "ocr_extract",
        "input_summary": f"upload_id={upload_id}",
        "output_summary": {"status": status, "field_count": len(extracted)},
        "performed_by": performed_by,
    }).execute()

    return result


def process_text_ocr(raw_text: str, draft_id: int | None, performed_by: int) -> dict:
    extracted, confidence = _heuristic_extract(raw_text)
    if OPENAI_API_KEY and len(raw_text) > 50:
        try:
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Extract fields from this OCR text:\n\n{raw_text}"},
                ],
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
                extracted = parsed.get("extracted_fields") or extracted
                confidence = parsed.get("field_confidence") or confidence
        except Exception:
            pass

    mapped = extraction_to_draft_fields(extracted)
    sb = get_supabase()
    row = sb.table("intake_extraction_results").insert({
        "draft_id": draft_id,
        "status": "completed" if extracted else "requires_review",
        "raw_text": raw_text,
        "extracted_fields": extracted,
        "field_confidence": confidence,
        "mapped_fields": mapped,
        "provider": "openai_text" if OPENAI_API_KEY else "heuristic",
    }).execute()
    ext = row.data[0]
    sb.table("intake_ai_logs").insert({
        "draft_id": draft_id,
        "action": "ocr_map_text",
        "performed_by": performed_by,
        "output_summary": {"extraction_id": ext["id"]},
    }).execute()
    return ext


def format_extraction_response(ext: dict) -> dict:
    fields = ext.get("extracted_fields") or {}
    conf = ext.get("field_confidence") or {}
    field_list: List[dict] = []
    for key in FIELD_KEYS:
        if key not in fields:
            continue
        score_raw = float(conf.get(key, 0.7))
        score_pct = round(score_raw * 100 if score_raw <= 1 else score_raw)
        field_list.append({
            "field": key,
            "label": FIELD_LABELS.get(key, key),
            "value": fields[key],
            "confidence": score_pct,
            "level": _confidence_level(score_raw if score_raw <= 1 else score_raw / 100),
        })

    raw_status = ext.get("status") or "processing"

    # Normalize status to one of: processing | completed | failed | requires_review
    if raw_status in ("completed", "failed", "processing", "requires_review"):
        status = raw_status
    elif field_list:
        status = "completed"
    else:
        status = "processing"

    msg = ext.get("error_message")
    if not msg and status == "requires_review":
        msg = "Review all fields before saving. AI assists extraction only."
    if not msg and status == "processing":
        msg = "OCR is still processing. Please wait and refresh."

    ext_id = ext.get("id")
    return {
        **ext,
        "id": ext_id,
        "extraction_id": ext_id,
        "status": status,
        "fields": field_list,
        "extracted_fields": fields,
        "field_confidence": conf,
        "mapped_fields": ext.get("mapped_fields") or {},
        "openai_available": bool(OPENAI_API_KEY),
        "message": msg,
    }
