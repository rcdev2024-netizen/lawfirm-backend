"""Load Philippine valid ID catalog from Supabase."""
from typing import Any, Dict, List

from database import get_supabase

# Fallback if table missing or empty
FALLBACK_PRIMARY = [
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
]

FALLBACK_SECONDARY = [
    "TIN ID",
    "Barangay ID",
    "Company ID",
    "School ID",
    "Police Clearance",
    "NBI Clearance",
    "Birth Certificate",
    "Marriage Certificate",
]


def fetch_valid_id_types() -> Dict[str, Any]:
    try:
        result = (
            get_supabase()
            .table("valid_id_types")
            .select("id, name, category, display_order")
            .eq("is_active", True)
            .order("category")
            .order("display_order")
            .execute()
        )
        rows = result.data or []
    except Exception:
        rows = []

    if not rows:
        return {
            "primary": FALLBACK_PRIMARY,
            "secondary": FALLBACK_SECONDARY,
            "id_types": FALLBACK_PRIMARY + FALLBACK_SECONDARY,
            "items": [
                *[{"id": None, "name": n, "category": "primary", "display_order": i} for i, n in enumerate(FALLBACK_PRIMARY, 1)],
                *[{"id": None, "name": n, "category": "secondary", "display_order": i} for i, n in enumerate(FALLBACK_SECONDARY, 1)],
            ],
        }

    primary: List[str] = []
    secondary: List[str] = []
    for r in rows:
        if r.get("category") == "primary":
            primary.append(r["name"])
        else:
            secondary.append(r["name"])

    return {
        "primary": primary,
        "secondary": secondary,
        "id_types": primary + secondary,
        "items": rows,
    }
