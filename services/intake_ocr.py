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


def _heuristic_extract(raw_text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """Rule-based fallback when no AI OCR provider is configured."""
    fields: Dict[str, Any] = {}
    confidence: Dict[str, float] = {}

    patterns = {
        "email": (r"[\w.+-]+@[\w.-]+\.\w+", "email", 0.9),
        "phoneNumber": (r"(?:\+63|0)?9\d{9}", "phoneNumber", 0.75),
        "birthDate": (r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", "birthDate", 0.5),
    }
    for key, (pat, field, conf) in patterns.items():
        m = re.search(pat, raw_text, re.I)
        if m and field not in fields:
            if field == "birthDate":
                d, mo, y = m.groups()
                y = y if len(y) == 4 else f"19{y}" if int(y) > 30 else f"20{y}"
                fields[field] = f"{y}-{int(mo):02d}-{int(d):02d}"
            else:
                fields[field] = m.group(0)
            confidence[field] = conf

    name_match = re.search(
        r"(?:name|client)[:\s]+([A-Za-z]+(?:\s+[A-Za-z.]+){1,4})",
        raw_text,
        re.I,
    )
    if name_match:
        parts = name_match.group(1).split()
        if len(parts) >= 2:
            fields["firstName"] = parts[0]
            fields["lastName"] = parts[-1]
            if len(parts) > 2:
                fields["middleName"] = " ".join(parts[1:-1])
            confidence["firstName"] = 0.55
            confidence["lastName"] = 0.55

    case_match = re.search(
        r"(family|criminal|civil|labor|corporate|immigration|annulment|divorce)",
        raw_text,
        re.I,
    )
    if case_match:
        fields["caseType"] = case_match.group(1).title()
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
