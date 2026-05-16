from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


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
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AppointmentStatusUpdate(BaseModel):
    status: str
