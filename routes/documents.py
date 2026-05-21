from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# List view excludes description (heavy text) — kept in detail endpoint
_DOC_LIST_COLS = "id,title,file_url,file_type,file_size,case_id,uploaded_by,is_confidential,created_at"


@router.post("", response_model=schemas.DocumentOut, summary="Upload/create a document record")
def create_document(
    doc: schemas.DocumentCreate,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    data = {
        "title": doc.title,
        "file_url": doc.file_url,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "case_id": doc.case_id,
        "uploaded_by": current_user["id"],
        "description": doc.description,
        "is_confidential": doc.is_confidential or False,
    }
    result = supabase.table("documents").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create document record")
    return result.data[0]


@router.get("", response_model=List[schemas.DocumentOut], summary="Get documents")
def get_documents(
    case_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    role = current_user.get("role", "client")
    query = supabase.table("documents").select(_DOC_LIST_COLS).order("created_at", desc=True).range(skip, skip + limit - 1)

    if case_id:
        query = query.eq("case_id", case_id)
    elif role == "client":
        result_cases = supabase.table("cases").select("id").eq("client_id", current_user["id"]).execute()
        case_ids = [c["id"] for c in (result_cases.data or [])]
        if not case_ids:
            return []
        query = query.in_("case_id", case_ids)

    items = query.execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


@router.get("/my", response_model=List[schemas.DocumentOut], summary="Get my documents")
def get_my_documents(current_user: dict = Depends(auth_utils.get_current_user)):
    result_cases = supabase.table("cases").select("id").eq("client_id", current_user["id"]).execute()
    case_ids = [c["id"] for c in (result_cases.data or [])]
    if not case_ids:
        return []
    items = supabase.table("documents").select(_DOC_LIST_COLS).in_("case_id", case_ids).order("created_at", desc=True).execute().data or []
    response = JSONResponse(content=items)
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


@router.get("/{doc_id}", response_model=schemas.DocumentOut, summary="Get document by ID")
def get_document(doc_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("documents").select("*").eq("id", doc_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return result.data[0]


@router.delete("/{doc_id}", summary="Delete a document")
def delete_document(doc_id: int, current_user: dict = Depends(auth_utils.get_current_user)):
    result = supabase.table("documents").select("*").eq("id", doc_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = result.data[0]
    role = current_user.get("role", "client")
    if role == "client" and doc.get("uploaded_by") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    supabase.table("documents").delete().eq("id", doc_id).execute()
    return {"message": f"Document {doc_id} deleted successfully"}
