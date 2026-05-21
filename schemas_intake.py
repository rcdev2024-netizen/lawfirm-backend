"""Pydantic schemas for client intake wizard and OCR workflow."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import date, datetime


# ── Wizard step payloads (stored in draft_data JSONB) ─────────

class PersonalInfoStep(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = None
    last_name: str = Field(..., min_length=1, max_length=100)
    suffix: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: date
    civil_status: Optional[str] = None
    nationality: str = Field(..., min_length=1)
    place_of_birth: Optional[str] = None
    occupation: Optional[str] = None


class ContactInfoStep(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., min_length=7, max_length=50)
    alternate_phone: Optional[str] = None
    address: str = Field(..., min_length=3)
    barangay: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Philippines"


class ValidIdItem(BaseModel):
    id_type: str
    id_number: str
    id_image_url: Optional[str] = None
    is_primary: bool = False


class ValidIdsStep(BaseModel):
    profile_photo_url: Optional[str] = None
    profile_photo_upload_id: Optional[int] = None
    photo_metadata: Optional[Dict[str, Any]] = None
    primary_id_type: Optional[str] = None
    primary_id_number: Optional[str] = None
    primary_id_image_url: Optional[str] = None
    primary_id_image_upload_id: Optional[int] = None
    secondary_id_type: Optional[str] = None
    secondary_id_number: Optional[str] = None
    secondary_id_image_url: Optional[str] = None
    secondary_id_image_upload_id: Optional[int] = None


class CaseInfoStep(BaseModel):
    case_type: str = Field(..., min_length=1)
    case_category: Optional[str] = None
    consultation_date: Optional[date] = None
    assigned_lawyer_id: Optional[int] = None
    referred_by: Optional[str] = None
    notes: Optional[str] = None
    priority_level: Literal["low", "medium", "high", "urgent"] = "medium"
    client_status: Literal["prospect", "active", "closed"] = "prospect"
    tags: Optional[List[str]] = None


class IntakeDraftData(BaseModel):
    personal: Optional[PersonalInfoStep] = None
    contact: Optional[ContactInfoStep] = None
    valid_ids: Optional[ValidIdsStep] = None
    case_info: Optional[CaseInfoStep] = None
    password: Optional[str] = Field(None, min_length=8, description="Portal password; auto-generated if omitted")


class IntakeDraftCreate(BaseModel):
    source: Literal["manual", "ocr"] = "manual"
    current_step: int = Field(1, ge=1, le=3)
    draft_data: Optional[Dict[str, Any]] = None


class IntakeDraftUpdate(BaseModel):
    current_step: Optional[int] = Field(None, ge=1, le=3)
    draft_data: Optional[Dict[str, Any]] = None
    status: Optional[Literal["draft", "abandoned"]] = None


class IntakeDraftOut(BaseModel):
    id: int
    created_by: Optional[int] = None
    status: str
    current_step: int
    source: str
    draft_data: Dict[str, Any]
    intake_upload_id: Optional[int] = None
    extraction_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedIntakeDraftsOut(BaseModel):
    items: List[IntakeDraftOut]
    total: int
    page: int
    limit: int
    pages: int


# ── Uploads & OCR ─────────────────────────────────────────────

class IntakeUploadOut(BaseModel):
    id: int
    upload_id: int
    url: Optional[str] = None
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_path: str
    public_url: Optional[str] = None
    upload_category: str
    draft_id: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "IntakeUploadOut":
        uid = row["id"]
        url = row.get("public_url") or row.get("storage_path")
        return cls(
            id=uid,
            upload_id=uid,
            url=url,
            file_name=row["file_name"],
            file_type=row.get("file_type"),
            file_size=row.get("file_size"),
            storage_path=row["storage_path"],
            public_url=row.get("public_url"),
            upload_category=row["upload_category"],
            draft_id=row.get("draft_id"),
            created_at=row.get("created_at"),
        )


class OcrProcessRequest(BaseModel):
    upload_id: int
    draft_id: Optional[int] = None


class OcrMapFromTextRequest(BaseModel):
    raw_text: str = Field(..., min_length=10)
    draft_id: Optional[int] = None


class ExtractionFieldOut(BaseModel):
    field: str
    label: Optional[str] = None
    value: Any
    confidence: float
    level: Optional[Literal["high", "medium", "low"]] = None


class OcrProcessOut(BaseModel):
    id: int
    extraction_id: int
    status: str = "processing"


class IntakeExtractionOut(BaseModel):
    id: int
    extraction_id: Optional[int] = None
    upload_id: Optional[int] = None
    draft_id: Optional[int] = None
    status: str
    openai_available: bool = False
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any]
    field_confidence: Dict[str, float]
    mapped_fields: Dict[str, Any]
    fields: List[ExtractionFieldOut]
    provider: Optional[str] = None
    error_message: Optional[str] = None
    reviewed: bool = False
    message: Optional[str] = None
    created_at: Optional[datetime] = None


class ApplyExtractionRequest(BaseModel):
    extraction_id: int
    draft_id: int
    overwrite: bool = False


# ── AI helpers ────────────────────────────────────────────────

class DuplicateCheckRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None


class DuplicateMatch(BaseModel):
    user_id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    match_score: float
    match_reasons: List[str]


class DuplicateCheckOut(BaseModel):
    has_duplicates: bool
    matches: List[DuplicateMatch]


class CaseClassifyRequest(BaseModel):
    notes: Optional[str] = None
    case_type: Optional[str] = None


class CaseClassifyOut(BaseModel):
    predicted_category: str
    confidence: float
    alternatives: List[str]
    reasoning: str


class IntakeSuggestionsRequest(BaseModel):
    draft_data: Dict[str, Any] = Field(default_factory=dict)
    current_step: int = Field(1, ge=1, le=3)


class IntakeSuggestion(BaseModel):
    field: str
    severity: Literal["info", "warning", "error"]
    message: str


class IntakeSuggestionsOut(BaseModel):
    suggestions: List[IntakeSuggestion]
    is_ready_to_finalize: bool


# ── Finalize & profile ────────────────────────────────────────

class IntakeFinalizeOut(BaseModel):
    client_id: int
    user_id: int
    email: str
    full_name: str
    temporary_password: Optional[str] = None
    client_profile: Optional[Dict[str, Any]] = None
    message: str = "Client created successfully."


class ClientProfileOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    approval_status: Optional[str] = None
    personal: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    valid_ids: Optional[List[Dict[str, Any]]] = None
    intake_cases: Optional[List[Dict[str, Any]]] = None
    photos: Optional[List[Dict[str, Any]]] = None
