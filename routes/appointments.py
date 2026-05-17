from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=schemas.AppointmentOut, summary="Book an appointment (public or authenticated)")
def create_appointment(
    appointment: schemas.AppointmentCreate,
    current_user: Optional[dict] = Depends(auth_utils.get_optional_user)
):
    data = {
        "full_name": appointment.full_name,
        "email": appointment.email,
        "phone": appointment.phone,
        "practice_area": appointment.practice_area,
        "message": appointment.message,
        "preferred_date": str(appointment.preferred_date) if appointment.preferred_date else None,
        "preferred_time": appointment.preferred_time,
        "appointment_type": appointment.appointment_type or "onsite",
        "status": "pending",
        "user_id": current_user["id"] if current_user else None
    }
    result = supabase.table("appointments").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to book appointment")
    return result.data[0]


@router.get("", response_model=List[schemas.AppointmentOut], summary="Get all appointments (admin/attorney)")
def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    appt_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")

    query = supabase.table("appointments").select("*").order("created_at", desc=True).range(skip, skip + limit - 1)
    if appt_status:
        query = query.eq("status", appt_status)
    result = query.execute()
    return result.data or []


@router.get("/my", response_model=List[schemas.AppointmentOut], summary="Get my appointments")
def get_my_appointments(current_user: dict = Depends(auth_utils.get_current_user)):
    role = current_user.get("role", "client")

    if role == "attorney":
        result = (
            supabase.table("appointments")
            .select("*")
            .eq("attorney_id", current_user["id"])
            .order("created_at", desc=True)
            .execute()
        )
    elif role == "admin":
        result = supabase.table("appointments").select("*").order("created_at", desc=True).execute()
    else:
        result = (
            supabase.table("appointments")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .execute()
        )
    return result.data or []


@router.get("/{appointment_id}", response_model=schemas.AppointmentOut, summary="Get appointment by ID")
def get_appointment(appointment_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return result.data[0]


@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentOut, summary="Update appointment status (admin/attorney)")
def update_appointment_status(
    appointment_id: int,
    body: schemas.AppointmentStatusUpdate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Admin or attorney access required")

    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    update_data: dict = {"status": body.status}
    if body.notes is not None:
        update_data["notes"] = body.notes

    result = supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return result.data[0]


@router.patch("/{appointment_id}", response_model=schemas.AppointmentOut, summary="Admin update: assign attorney and status")
def admin_update_appointment(
    appointment_id: int,
    body: schemas.AppointmentAdminUpdate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    update_data: dict = {}
    if body.status is not None:
        valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
        if body.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
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
    return result.data[0]


@router.delete("/{appointment_id}", summary="Delete an appointment (admin)")
def delete_appointment(appointment_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    result = supabase.table("appointments").delete().eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return {"message": f"Appointment {appointment_id} deleted successfully"}
