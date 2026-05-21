from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils
from services.emailjs import send_appointment_notification
from services.textbee import send_sms_notification
from datetime import date

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

VALID_STATUSES = ["pending", "confirmed", "cancelled", "completed", "rescheduled", "expired"]

# List view excludes message (client's original inquiry text — heavy, not shown in list)
_APPT_LIST_COLS = "id,full_name,email,phone,practice_area,preferred_date,preferred_time,appointment_type,status,notes,user_id,attorney_id,created_at"


@router.post(
    "",
    response_model=schemas.AppointmentOut,
    summary="Book an appointment (public or authenticated)",
)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(auth_utils.get_optional_user),
):
    data = {
        "full_name":        appointment.full_name,
        "email":            appointment.email,
        "phone":            appointment.phone,
        "practice_area":    appointment.practice_area,
        "message":          appointment.message,
        "preferred_date":   str(appointment.preferred_date) if appointment.preferred_date else None,
        "preferred_time":   appointment.preferred_time,
        "appointment_type": appointment.appointment_type or "onsite",
        "status":           "pending",
        "user_id":          current_user["id"] if current_user else None,
    }
    result = supabase.table("appointments").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to book appointment")
    appt = result.data[0]
    background_tasks.add_task(send_appointment_notification, "New Booking", appt)
    background_tasks.add_task(send_sms_notification, "New Booking", appt)
    return appt


@router.get(
    "",
    response_model=List[schemas.AppointmentOut],
    summary="Get all appointments (admin/attorney) with optional filters",
)
def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    appt_status: Optional[str] = Query(None, alias="status"),
    date_from: Optional[str] = Query(None, description="Filter preferred_date >= (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter preferred_date <= (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search full_name, email, practice_area"),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")

    query = (
        supabase.table("appointments")
        .select(_APPT_LIST_COLS)
        .order("preferred_date", desc=False)
        .order("preferred_time", desc=False)
        .range(skip, skip + limit - 1)
    )
    if appt_status:
        query = query.eq("status", appt_status)
    if date_from:
        query = query.gte("preferred_date", date_from)
    if date_to:
        query = query.lte("preferred_date", date_to)
    if search:
        query = query.ilike("full_name", f"%{search}%")

    items = query.execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=30"
    return response


@router.get(
    "/my",
    response_model=List[schemas.AppointmentOut],
    summary="Get my appointments with optional filters",
)
def get_my_appointments(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    appt_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    role = current_user.get("role", "client")

    if role == "attorney":
        query = supabase.table("appointments").select(_APPT_LIST_COLS).eq("attorney_id", current_user["id"])
    elif role == "admin":
        query = supabase.table("appointments").select(_APPT_LIST_COLS)
    else:
        query = supabase.table("appointments").select(_APPT_LIST_COLS).eq("user_id", current_user["id"])

    query = query.order("preferred_date", desc=False).order("preferred_time", desc=False)

    if appt_status:
        query = query.eq("status", appt_status)
    if date_from:
        query = query.gte("preferred_date", date_from)
    if date_to:
        query = query.lte("preferred_date", date_to)

    items = query.execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=30"
    return response


@router.post(
    "/expire-stale",
    summary="Mark past pending/confirmed appointments as expired (admin or cron)",
)
def expire_stale_appointments(
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    today = str(date.today())
    # Mark pending/confirmed appointments whose date has passed as expired
    result = (
        supabase.table("appointments")
        .update({"status": "expired"})
        .lt("preferred_date", today)
        .in_("status", ["pending", "confirmed"])
        .execute()
    )
    count = len(result.data) if result.data else 0
    return {"expired_count": count, "message": f"{count} appointment(s) marked as expired"}


@router.post(
    "/{appointment_id}/reschedule",
    response_model=schemas.AppointmentOut,
    summary="Reschedule an appointment — marks original as rescheduled, creates new pending",
)
def reschedule_appointment(
    appointment_id: int,
    body: schemas.AppointmentReschedule,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")

    # Fetch original
    fetch = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
    if not fetch.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    original = fetch.data[0]

    # Mark original as rescheduled
    supabase.table("appointments").update({
        "status": "rescheduled",
        "notes": f"Rescheduled to {body.new_date} at {body.new_time or 'TBD'}. {body.reason or ''}".strip()
    }).eq("id", appointment_id).execute()

    # Create new appointment with new date/time, linked back
    new_data = {
        "full_name":        original["full_name"],
        "email":            original["email"],
        "phone":            original.get("phone"),
        "practice_area":    original.get("practice_area"),
        "message":          original.get("message"),
        "preferred_date":   str(body.new_date),
        "preferred_time":   body.new_time,
        "appointment_type": original.get("appointment_type", "onsite"),
        "status":           "pending",
        "user_id":          original.get("user_id"),
        "attorney_id":      original.get("attorney_id"),
        "notes":            f"Rescheduled from appointment #{appointment_id}. {body.reason or ''}".strip(),
        "rescheduled_from_id": appointment_id,
    }
    new_result = supabase.table("appointments").insert(new_data).execute()
    if not new_result.data:
        raise HTTPException(status_code=500, detail="Failed to create rescheduled appointment")

    new_appt = new_result.data[0]
    background_tasks.add_task(send_appointment_notification, "Rescheduled", new_appt)
    background_tasks.add_task(send_sms_notification, "Rescheduled", new_appt)
    return new_appt


@router.get(
    "/{appointment_id}",
    response_model=schemas.AppointmentOut,
    summary="Get appointment by ID",
)
def get_appointment(
    appointment_id: int,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    result = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return result.data[0]


@router.patch(
    "/{appointment_id}/status",
    response_model=schemas.AppointmentOut,
    summary="Update appointment status (admin/attorney)",
)
def update_appointment_status(
    appointment_id: int,
    body: schemas.AppointmentStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")

    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")

    update_data: dict = {"status": body.status}
    if body.notes is not None:
        update_data["notes"] = body.notes

    result = supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt = result.data[0]
    background_tasks.add_task(send_appointment_notification, f"Status → {body.status.capitalize()}", appt)
    background_tasks.add_task(send_sms_notification, f"Status → {body.status.capitalize()}", appt)
    return appt


@router.patch(
    "/{appointment_id}",
    response_model=schemas.AppointmentOut,
    summary="Admin update: assign attorney, status, notes",
)
def admin_update_appointment(
    appointment_id: int,
    body: schemas.AppointmentAdminUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    update_data: dict = {}
    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        update_data["status"] = body.status
    if body.attorney_id is not None:
        update_data["attorney_id"] = body.attorney_id
        if "status" not in update_data:
            update_data["status"] = "confirmed"
    if body.notes is not None:
        update_data["notes"] = body.notes

    if not update_data:
        result = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return result.data[0]

    result = supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt = result.data[0]
    background_tasks.add_task(send_appointment_notification, "Admin Updated", appt)
    background_tasks.add_task(send_sms_notification, "Admin Updated", appt)
    return appt


@router.delete(
    "/{appointment_id}",
    summary="Delete an appointment (admin)",
)
def delete_appointment(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth_utils.get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    fetch = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
    if not fetch.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt = fetch.data[0]
    result = supabase.table("appointments").delete().eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    background_tasks.add_task(send_appointment_notification, "Deleted", appt)
    background_tasks.add_task(send_sms_notification, "Deleted", appt)
    return {"message": f"Appointment {appointment_id} deleted successfully"}
