"""
EmailJS notification service.

Sends appointment notifications to the law firm admin via the EmailJS REST API.
Called as a FastAPI BackgroundTask so it never blocks the API response.

EmailJS REST endpoint:
  POST https://api.emailjs.com/api/v1.0/email/send
  Content-Type: application/json

Template variables used (must match the EmailJS template):
  {{to_email}}            – recipient (admin)
  {{transaction_type}}    – e.g. "New Booking", "Status Updated", "Deleted"
  {{appointment_id}}
  {{client_name}}
  {{client_email}}
  {{client_phone}}
  {{practice_area}}
  {{preferred_date}}
  {{preferred_time}}
  {{appointment_type}}    – onsite / online
  {{status}}
  {{notes}}
  {{attorney_id}}
  {{message}}             – client's original message
"""

import logging
import httpx

logger = logging.getLogger(__name__)

# ── EmailJS credentials ────────────────────────────────────────────────────────
_EMAILJS_URL        = "https://api.emailjs.com/api/v1.0/email/send"
_SERVICE_ID         = "service_rkqrqht"
_TEMPLATE_ID        = "template_appointments"   # set this after creating the template
_PUBLIC_KEY         = "t4w0fMIgnyUuZ6qKa"
_PRIVATE_KEY        = "fXmVgdVNsAIvccZSL8NFj"
_ADMIN_EMAIL        = "rochellemariecortez@gmail.com"

# ── Timeout (seconds) ─────────────────────────────────────────────────────────
_TIMEOUT = 10


def _build_params(transaction_type: str, appt: dict) -> dict:
    """Map an appointment dict to EmailJS template variables."""
    return {
        "to_email":         _ADMIN_EMAIL,
        "transaction_type": transaction_type,
        "appointment_id":   str(appt.get("id", "N/A")),
        "client_name":      appt.get("full_name", "N/A"),
        "client_email":     appt.get("email", "N/A"),
        "client_phone":     appt.get("phone") or "N/A",
        "practice_area":    appt.get("practice_area") or "N/A",
        "preferred_date":   str(appt.get("preferred_date")) if appt.get("preferred_date") else "N/A",
        "preferred_time":   appt.get("preferred_time") or "N/A",
        "appointment_type": appt.get("appointment_type") or "onsite",
        "status":           appt.get("status", "N/A"),
        "notes":            appt.get("notes") or "—",
        "attorney_id":      str(appt.get("attorney_id")) if appt.get("attorney_id") else "Unassigned",
        "message":          appt.get("message") or "—",
    }


def send_appointment_notification(transaction_type: str, appt: dict) -> None:
    """
    Fire-and-forget email notification.
    Designed to run inside a FastAPI BackgroundTask.

    Args:
        transaction_type: Human-readable label, e.g. "New Booking", "Cancelled"
        appt: The appointment dict returned from Supabase
    """
    payload = {
        "service_id":       _SERVICE_ID,
        "template_id":      _TEMPLATE_ID,
        "user_id":          _PUBLIC_KEY,
        "accessToken":      _PRIVATE_KEY,
        "template_params":  _build_params(transaction_type, appt),
    }

    try:
        response = httpx.post(
            _EMAILJS_URL,
            json=payload,
            timeout=_TIMEOUT,
        )
        if response.status_code == 200:
            logger.info(
                "EmailJS notification sent | type=%s | appointment_id=%s",
                transaction_type,
                appt.get("id"),
            )
        else:
            logger.warning(
                "EmailJS returned non-200 | status=%s | body=%s",
                response.status_code,
                response.text,
            )
    except httpx.TimeoutException:
        logger.error("EmailJS request timed out | type=%s | appointment_id=%s", transaction_type, appt.get("id"))
    except httpx.RequestError as exc:
        logger.error("EmailJS request failed | error=%s", str(exc))
