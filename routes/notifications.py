from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=List[schemas.NotificationOut], summary="Get my notifications")
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    query = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )
    if unread_only:
        query = query.eq("is_read", False)
    result = query.execute()
    return result.data or []


@router.patch("/{notif_id}/read", response_model=schemas.NotificationOut, summary="Mark notification as read")
def mark_read(notif_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("notifications").select("*").eq("id", notif_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    if result.data[0].get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = supabase.table("notifications").update({"is_read": True}).eq("id", notif_id).execute()
    return updated.data[0]


@router.patch("/read-all", summary="Mark all notifications as read")
def mark_all_read(current_user: dict = Depends(auth_utils.get_current_user)):
    supabase.table("notifications").update({"is_read": True}).eq("user_id", current_user["id"]).eq("is_read", False).execute()
    return {"message": "All notifications marked as read"}


@router.delete("/{notif_id}", summary="Delete a notification")
def delete_notification(notif_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("notifications").select("*").eq("id", notif_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    if result.data[0].get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    supabase.table("notifications").delete().eq("id", notif_id).execute()
    return {"message": "Notification deleted"}
