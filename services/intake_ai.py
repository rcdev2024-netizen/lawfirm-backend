"""AI-assisted duplicate detection, case classification, and form suggestions."""
import re
from typing import Any, Dict, List

from database import get_supabase
from services.intake_helpers import (
    CASE_CATEGORIES,
    build_full_name,
    normalize_phone,
    parse_draft_data,
    validate_step,
)


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


def build_suggestions(draft_data: Dict[str, Any]) -> tuple[List[dict], bool]:
    suggestions: List[dict] = []
    data = parse_draft_data(draft_data)

    for step in range(1, 5):
        for err in validate_step(step, draft_data):
            suggestions.append({"field": f"step{step}", "severity": "error", "message": err})

    if data.contact:
        c = data.contact
        if c.phone_number and not re.match(r"^(\+63|0)?9\d{9}$", normalize_phone(c.phone_number).replace(" ", "")):
            suggestions.append({
                "field": "phoneNumber",
                "severity": "warning",
                "message": "Phone number may be invalid for Philippines (expected 09XXXXXXXXX).",
            })
        if c.address and len(c.address) < 10:
            suggestions.append({
                "field": "address",
                "severity": "warning",
                "message": "Address looks incomplete.",
            })
        if not c.city and not c.province:
            suggestions.append({
                "field": "city",
                "severity": "info",
                "message": "Consider adding city and province for complete address.",
            })

    if data.case_info and data.case_info.notes:
        pred = classify_case(data.case_info.notes, data.case_info.case_type)
        if not data.case_info.case_category:
            suggestions.append({
                "field": "caseCategory",
                "severity": "info",
                "message": f"Suggested category: {pred['predicted_category']}",
            })

    errors = [s for s in suggestions if s["severity"] == "error"]
    ready = len(errors) == 0 and validate_step(4, draft_data) == []
    return suggestions, ready
