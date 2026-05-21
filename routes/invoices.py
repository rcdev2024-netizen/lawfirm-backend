from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

# Columns for list views — excludes notes (heavy text)
_INVOICE_LIST_COLS = "id,invoice_number,client_id,case_id,amount,tax,total,status,due_date,paid_date,created_at"


@router.post("", response_model=schemas.InvoiceOut, summary="Create invoice (admin/attorney)")
def create_invoice(
    invoice: schemas.InvoiceCreate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Only attorneys or admins can create invoices")

    data = {
        "invoice_number": invoice.invoice_number,
        "client_id": invoice.client_id,
        "case_id": invoice.case_id,
        "amount": float(invoice.amount),
        "tax": float(invoice.tax or 0),
        "total": float(invoice.total),
        "status": invoice.status or "unpaid",
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "notes": invoice.notes,
    }
    result = supabase.table("invoices").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create invoice")

    notif_data = {
        "user_id": invoice.client_id,
        "type": "invoice",
        "title": f"New invoice #{invoice.invoice_number} generated",
        "body": f"Amount due: {invoice.total}",
        "is_read": False,
        "link": "/dashboard/billing",
    }
    supabase.table("notifications").insert(notif_data).execute()

    return result.data[0]


@router.get("", response_model=List[schemas.InvoiceOut], summary="Get invoices")
def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    inv_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    role = current_user.get("role", "client")
    query = supabase.table("invoices").select(_INVOICE_LIST_COLS).order("created_at", desc=True).range(skip, skip + limit - 1)

    if role == "client":
        query = query.eq("client_id", current_user["id"])
    if inv_status:
        query = query.eq("status", inv_status)

    items = query.execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


@router.get("/my", response_model=List[schemas.InvoiceOut], summary="Get my invoices")
def get_my_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    items = supabase.table("invoices").select(_INVOICE_LIST_COLS).eq("client_id", current_user["id"]).order("created_at", desc=True).range(skip, skip + limit - 1).execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut, summary="Get invoice by ID")
def get_invoice(invoice_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("invoices").select("*").eq("id", invoice_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = result.data[0]
    if current_user.get("role") == "client" and inv.get("client_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return inv


@router.patch("/{invoice_id}/status", response_model=schemas.InvoiceOut, summary="Update invoice status")
def update_invoice_status(
    invoice_id: int,
    body: schemas.InvoiceStatusUpdate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    if current_user.get("role") not in ("admin", "attorney"):
        raise HTTPException(status_code=403, detail="Only attorneys or admins can update invoices")
    valid = ["unpaid", "paid", "overdue", "cancelled"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid)}")
    update_data: dict = {"status": body.status}
    if body.paid_date:
        update_data["paid_date"] = str(body.paid_date)
    result = supabase.table("invoices").update(update_data).eq("id", invoice_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result.data[0]
