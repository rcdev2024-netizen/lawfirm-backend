"""AI-assisted duplicate detection, case classification, and form suggestions."""
import re
from typing import Any, Dict, List, Set

from database import get_supabase
from services.intake_helpers import (
    CASE_CATEGORIES,
    build_full_name,
    normalize_phone,
)
from services.intake_validation import validate_step_only


def _name_similarity(a: str, b: str) -> float:
    a_set = set(a.lower().split())
    b_set = set(b.lower().split())
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / max(len(a_set), len(b_set))


def check_duplicates(
    first_name: str | None,
    middle_name: str | None,
    last_name: str | None,
    email: str | None,
    phone_number: str | None,
) -> List[dict]:
    sb = get_supabase()
    role = sb.table("roles").select("id").eq("name", "client").execute()
    if not role.data:
        return []
    client_role_id = role.data[0]["id"]

    users = (
        sb.table("users")
        .select("id, full_name, email, phone")
        .eq("role_id", client_role_id)
        .limit(500)
        .execute()
    ).data or []

    target_name = build_full_name(
        first_name or "",
        middle_name,
        last_name or "",
    ).strip()
    target_phone = normalize_phone(phone_number) if phone_number else ""
    matches: List[dict] = []

    for u in users:
        reasons: List[str] = []
        score = 0.0

        if email and u.get("email") and email.lower() == u["email"].lower():
            score = max(score, 1.0)
            reasons.append("exact email match")

        if target_phone and u.get("phone"):
            up = normalize_phone(u["phone"])
            if target_phone == up:
                score = max(score, 0.95)
                reasons.append("exact phone match")

        if target_name and u.get("full_name"):
            sim = _name_similarity(target_name, u["full_name"])
            if sim >= 0.7:
                score = max(score, sim)
                reasons.append(f"name similarity {sim:.0%}")

        if score >= 0.7:
            matches.append({
                "user_id": u["id"],
                "full_name": u["full_name"],
                "email": u.get("email"),
                "phone": u.get("phone"),
                "match_score": round(score, 2),
                "match_reasons": reasons,
            })

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:10]


def classify_case(notes: str | None, case_type: str | None) -> dict:
    text = f"{case_type or ''} {notes or ''}".lower()
    rules = [
        (["annulment", "divorce", "custody", "family", "adoption"], "Family Law", 0.9),
        (["theft", "drug", "criminal", "arrest", "bail"], "Criminal Law", 0.88),
        (["contract", "breach", "civil", "damages"], "Civil Law", 0.85),
        (["termination", "labor", "employ", "salary", "dole"], "Labor Law", 0.87),
        (["corporation", "sec", "business", "partnership"], "Corporate Law", 0.86),
        (["visa", "immigration", "deport"], "Immigration", 0.84),
        (["title", "land", "property", "real estate"], "Real Estate", 0.83),
    ]
    best = "Other"
    best_score = 0.4
    alts: List[str] = []

    for keywords, category, conf in rules:
        if any(k in text for k in keywords):
            if conf > best_score:
                if best != "Other":
                    alts.append(best)
                best = category
                best_score = conf
            elif category not in alts:
                alts.append(category)

    reasoning = (
        f"Classified as {best} based on keywords in case type/notes."
        if text.strip()
        else "Provide case type or notes for better classification."
    )
    return {
        "predicted_category": best,
        "confidence": best_score,
        "alternatives": alts[:3] or [c for c in CASE_CATEGORIES if c != best][:2],
        "reasoning": reasoning,
    }


def _dedupe_suggestions(items: List[dict]) -> List[dict]:
    seen: Set[str] = set()
    out: List[dict] = []
    for s in items:
        key = f"{s.get('field')}:{s.get('message')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def build_suggestions(
    draft_data: Dict[str, Any],
    current_step: int = 1,
) -> tuple[List[dict], bool]:
    """Hints for the active step only — no errors for empty future steps."""
    suggestions: List[dict] = []
    step = max(1, min(4, current_step))

    for e in validate_step_only(step, draft_data):
        suggestions.append({
            "field": e["field"],
            "severity": "error",
            "message": e["message"],
        })

    if step == 1:
        p = draft_data.get("personal") or {}
        if p and not p.get("middle_name"):
            suggestions.append({
                "field": "personal.middle_name",
                "severity": "info",
                "message": "Middle name is optional but helps match records.",
            })

    if step == 2:
        c = draft_data.get("contact") or {}
        if c:
            phone = c.get("phone_number")
            if phone and not re.match(
                r"^(\+63|0)?9\d{9}$", normalize_phone(str(phone)).replace(" ", "")
            ):
                suggestions.append({
                    "field": "contact.phone_number",
                    "severity": "warning",
                    "message": "Phone number may be invalid for Philippines (expected 09XXXXXXXXX).",
                })
            if c.get("address") and len(str(c["address"])) < 10:
                suggestions.append({
                    "field": "contact.address",
                    "severity": "warning",
                    "message": "Address looks incomplete.",
                })
            if not c.get("city") and not c.get("province"):
                suggestions.append({
                    "field": "contact.city",
                    "severity": "info",
                    "message": "Consider adding city and province for a complete address.",
                })

    if step == 3:
        v = draft_data.get("valid_ids") or {}
        if not v.get("profile_photo_upload_id") and not v.get("profile_photo_url"):
            suggestions.append({
                "field": "valid_ids.profile_photo_upload_id",
                "severity": "info",
                "message": "A profile photo helps staff identify the client.",
            })

    if step == 4:
        ci = draft_data.get("case_info") or {}
        if ci.get("notes") and not ci.get("case_category"):
            pred = classify_case(ci.get("notes"), ci.get("case_type"))
            suggestions.append({
                "field": "case_info.case_category",
                "severity": "info",
                "message": f"Suggested category: {pred['predicted_category']}",
            })

    suggestions = _dedupe_suggestions(suggestions)
    from services.intake_validation import validate_all_steps

    ready = len(validate_all_steps(draft_data)) == 0
    return suggestions, ready
