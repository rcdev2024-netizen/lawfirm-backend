from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/messages", tags=["Messages"])

# List view excludes body — only fetched when opening a single message
_MSG_LIST_COLS = "id,sender_id,recipient_id,case_id,subject,is_read,parent_id,created_at"


@router.post("", response_model=schemas.MessageOut, summary="Send a message")
def send_message(
    msg: schemas.MessageCreate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    data = {
        "sender_id": current_user["id"],
        "recipient_id": msg.recipient_id,
        "case_id": msg.case_id,
        "subject": msg.subject,
        "body": msg.body,
        "is_read": False,
        "parent_id": msg.parent_id,
    }
    result = supabase.table("messages").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to send message")

    notif_data = {
        "user_id": msg.recipient_id,
        "type": "message",
        "title": f"New message from {current_user['full_name']}",
        "body": msg.subject or msg.body[:80],
        "is_read": False,
        "link": "/dashboard/messages",
    }
    supabase.table("notifications").insert(notif_data).execute()

    return result.data[0]


@router.get("/inbox", response_model=List[schemas.MessageOut], summary="Get my inbox")
def get_inbox(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    items = (
        supabase.table("messages")
        .select(_MSG_LIST_COLS)
        .eq("recipient_id", current_user["id"])
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    ).data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=30"
    return response


@router.get("/sent", response_model=List[schemas.MessageOut], summary="Get sent messages")
def get_sent(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    items = (
        supabase.table("messages")
        .select(_MSG_LIST_COLS)
        .eq("sender_id", current_user["id"])
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    ).data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=30"
    return response


@router.patch("/{message_id}/read", response_model=schemas.MessageOut, summary="Mark message as read")
def mark_read(message_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("messages").select("*").eq("id", message_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Message not found")
    msg = result.data[0]
    if msg.get("recipient_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = supabase.table("messages").update({"is_read": True}).eq("id", message_id).execute()
    return updated.data[0]


@router.get("/{message_id}", response_model=schemas.MessageOut, summary="Get message by ID")
def get_message(message_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("messages").select("*").eq("id", message_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Message not found")
    msg = result.data[0]
    uid = current_user["id"]
    if msg.get("sender_id") != uid and msg.get("recipient_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")
    return msg
