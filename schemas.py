from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ── AUTH SCHEMAS ──────────────────────────────────────────────

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "client"
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role_id: Optional[int] = None
    role: Optional[str] = "client"
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── APPOINTMENT SCHEMAS ────────────────────────────────────────

class AppointmentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    practice_area: Optional[str] = None
    message: str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    practice_area: Optional[str] = None
    message: str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None
    status: str
    user_id: Optional[int] = None
    attorney_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


# ── CASE SCHEMAS ───────────────────────────────────────────────

class CaseCreate(BaseModel):
    case_number: str
    case_name: str
    case_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "open"
    client_id: Optional[int] = None
    attorney_id: Optional[int] = None
    next_hearing_date: Optional[date] = None
    next_hearing_time: Optional[str] = None
    court: Optional[str] = None
    judge: Optional[str] = None
    filed_date: Optional[date] = None


class CaseUpdate(BaseModel):
    case_name: Optional[str] = None
    case_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    attorney_id: Optional[int] = None
    next_hearing_date: Optional[date] = None
    next_hearing_time: Optional[str] = None
    court: Optional[str] = None
    judge: Optional[str] = None
    closed_date: Optional[date] = None


class CaseOut(BaseModel):
    id: int
    case_number: str
    case_name: str
    case_type: Optional[str] = None
    description: Optional[str] = None
    status: str
    client_id: Optional[int] = None
    attorney_id: Optional[int] = None
    next_hearing_date: Optional[date] = None
    next_hearing_time: Optional[str] = None
    court: Optional[str] = None
    judge: Optional[str] = None
    filed_date: Optional[date] = None
    closed_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── DOCUMENT SCHEMAS ────────────────────────────────────────────

class DocumentCreate(BaseModel):
    title: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    case_id: Optional[int] = None
    description: Optional[str] = None
    is_confidential: Optional[bool] = False


class DocumentOut(BaseModel):
    id: int
    title: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    case_id: Optional[int] = None
    uploaded_by: Optional[int] = None
    description: Optional[str] = None
    is_confidential: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── MESSAGE SCHEMAS ─────────────────────────────────────────────

class MessageCreate(BaseModel):
    recipient_id: int
    case_id: Optional[int] = None
    subject: Optional[str] = None
    body: str
    parent_id: Optional[int] = None


class MessageOut(BaseModel):
    id: int
    sender_id: Optional[int] = None
    recipient_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: Optional[str] = None
    body: str
    is_read: bool
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── NOTIFICATION SCHEMAS ────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: Optional[str] = None
    title: str
    body: Optional[str] = None
    is_read: bool
    link: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── INVOICE SCHEMAS ─────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    invoice_number: str
    client_id: int
    case_id: Optional[int] = None
    amount: Decimal
    tax: Optional[Decimal] = Decimal("0")
    total: Decimal
    status: Optional[str] = "unpaid"
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    client_id: Optional[int] = None
    case_id: Optional[int] = None
    amount: Decimal
    tax: Decimal
    total: Decimal
    status: str
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvoiceStatusUpdate(BaseModel):
    status: str
    paid_date: Optional[date] = None


# ── ROLE SCHEMAS ────────────────────────────────────────────────

VALID_ROLES = {"guest", "client", "paralegal", "attorney", "admin"}


class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleOut(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RolePermissionCreate(BaseModel):
    permission: str


class RolePermissionOut(BaseModel):
    id: int
    role_name: str
    permission: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserRoleUpdate(BaseModel):
    role: str
    reason: Optional[str] = None


class UserRoleOut(BaseModel):
    id: int
    full_name: str
    email: str
    role_id: Optional[int] = None
    role: Optional[str] = "client"
    phone: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleAuditOut(BaseModel):
    id: int
    user_id: int
    changed_by: Optional[int] = None
    old_role_id: Optional[int] = None
    new_role_id: int
    reason: Optional[str] = None
    changed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── DASHBOARD SCHEMAS ───────────────────────────────────────────

class DashboardStats(BaseModel):
    active_cases: int
    upcoming_appointments: int
    total_documents: int
    unpaid_invoices: int
    unread_messages: int
    unread_notifications: int
