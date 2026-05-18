from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from database import supabase
import schemas
import auth as auth_utils
import math

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/unread-count", response_model=schemas.NotificationCountOut, summary="Get unread notification count")
def get_unread_count(current_user: dict = Depends(auth_utils.get_current_user)):
    result = (
        supabase.table("notifications")
        .select("id", count="exact")
        .eq("user_id", current_user["id"])
        .eq("is_read", False)
        .execute()
    )
    return schemas.NotificationCountOut(unread_count=result.count or 0)


@router.get("", response_model=schemas.PaginatedNotificationsOut, summary="Get my notifications (paginated)")
def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    unread_only: bool = Query(False),
    current_user: dict = Depends(auth_utils.get_current_user),
):
    skip = (page - 1) * limit

    count_q = supabase.table("notifications").select("id", count="exact").eq("user_id", current_user["id"])
    data_q = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )

    if unread_only:
        count_q = count_q.eq("is_read", False)
        data_q = data_q.eq("is_read", False)

    total = count_q.execute().count or 0
    items = data_q.execute().data or []

    return schemas.PaginatedNotificationsOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )


@router.get("/top", response_model=List[schemas.NotificationOut], summary="Get top 10 recent notifications (for dropdown)")
def get_top_notifications(current_user: dict = Depends(auth_utils.get_current_user)):
    result = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
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
