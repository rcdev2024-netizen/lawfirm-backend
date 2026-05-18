"""
TextBee SMS notification service.

Sends appointment notifications to the law firm admin via TextBee gateway.
Called as a FastAPI BackgroundTask so it never blocks the API response.

API: https://api.textbee.dev/api/v1/gateway/devices/{DEVICE_ID}/send-sms
"""

import logging
import requests

logger = logging.getLogger(__name__)

# ── TextBee credentials ────────────────────────────────────────────────────────
_BASE_URL  = "https://api.textbee.dev/api/v1"
_API_KEY   = "58b92f01-06b5-425b-a33f-c267ffb7dfcf"
_DEVICE_ID = "6a0b0bc99b9db0a6fe27740d"
_ADMIN_NUMBER = "+639154868899"

# ── Timeout (seconds) ─────────────────────────────────────────────────────────
_TIMEOUT = 30


def _compose_message(transaction_type: str, appt: dict) -> str:
    """Compose a concise SMS message from appointment data."""
    appt_id    = appt.get("id", "N/A")
    client     = appt.get("full_name", "N/A")
    area       = appt.get("practice_area") or "N/A"
    date       = str(appt.get("preferred_date")) if appt.get("preferred_date") else "N/A"
    time       = appt.get("preferred_time") or "N/A"
    mode       = (appt.get("appointment_type") or "onsite").capitalize()
    status     = (appt.get("status") or "pending").capitalize()
    attorney   = str(appt.get("attorney_id")) if appt.get("attorney_id") else "Unassigned"
    notes      = appt.get("notes") or "—"

    if transaction_type == "New Booking":
        return (
            f"[CortezLaw] NEW APPOINTMENT #{appt_id}\n"
            f"Client: {client}\n"
            f"Area: {area}\n"
            f"Date: {date} | {time}\n"
            f"Mode: {mode} | Status: {status}\n"
            f"Awaiting your approval."
        )
    elif transaction_type.startswith("Status Updated"):
        return (
            f"[CortezLaw] APPOINTMENT UPDATE #{appt_id}\n"
            f"Client: {client}\n"
            f"Status: {status}\n"
            f"Date: {date} | {time}\n"
            f"Notes: {notes}"
        )
    elif transaction_type == "Admin Updated":
        return (
            f"[CortezLaw] APPOINTMENT UPDATED #{appt_id}\n"
            f"Client: {client}\n"
            f"Attorney: {attorney}\n"
            f"Status: {status}\n"
            f"Date: {date} | {time}"
        )
    elif transaction_type == "Deleted":
        return (
            f"[CortezLaw] APPOINTMENT DELETED #{appt_id}\n"
            f"Client: {client}\n"
            f"Area: {area}\n"
            f"Date: {date} | {time}\n"
            f"This appointment has been removed."
        )
    else:
        return (
            f"[CortezLaw] APPOINTMENT NOTICE #{appt_id}\n"
            f"Type: {transaction_type}\n"
            f"Client: {client}\n"
            f"Status: {status}"
        )


def send_sms_notification(transaction_type: str, appt: dict) -> None:
    """
    Fire-and-forget SMS notification.
    Designed to run inside a FastAPI BackgroundTask.

    Args:
        transaction_type: Human-readable label, e.g. "New Booking", "Deleted"
        appt: The appointment dict returned from Supabase
    """
    url     = f"{_BASE_URL}/gateway/devices/{_DEVICE_ID}/send-sms"
    message = _compose_message(transaction_type, appt)

    payload = {
        "recipients": [_ADMIN_NUMBER],
        "message":    message,
    }
    headers = {
        "x-api-key":    _API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
        response.raise_for_status()
        logger.info(
            "TextBee SMS sent | type=%s | appointment_id=%s",
            transaction_type,
            appt.get("id"),
        )
    except requests.exceptions.HTTPError as e:
        logger.error(
            "TextBee HTTP error | status=%s | body=%s",
            e.response.status_code if e.response else "N/A",
            e.response.text if e.response else str(e),
        )
    except requests.exceptions.RequestException as e:
        logger.error("TextBee request failed | error=%s", str(e))
