from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=schemas.AppointmentOut, summary="Book an appointment (public)")
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
        "status": "pending",
        "user_id": current_user["id"] if current_user else None
    }
    result = supabase.table("appointments").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to book appointment")
    return result.data[0]


@router.get("", response_model=List[schemas.AppointmentOut], summary="Get all appointments (auth required)")
def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    appt_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    query = supabase.table("appointments").select("*").order("created_at", desc=True).range(skip, skip + limit - 1)
    if appt_status:
        query = query.eq("status", appt_status)
    result = query.execute()
    return result.data or []


@router.get("/my", response_model=List[schemas.AppointmentOut], summary="Get my appointments")
def get_my_appointments(current_user: dict = Depends(auth_utils.get_current_user)):
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


@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentOut, summary="Update appointment status")
def update_appointment_status(
    appointment_id: int,
    body: schemas.AppointmentStatusUpdate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    result = supabase.table("appointments").update({"status": body.status}).eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return result.data[0]


@router.delete("/{appointment_id}", summary="Delete an appointment")
def delete_appointment(appointment_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("appointments").delete().eq("id", appointment_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return {"message": f"Appointment {appointment_id} deleted successfully"}
