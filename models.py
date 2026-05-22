from sqlalchemy import Column, Integer, String, Boolean, Text, Date, ForeignKey, Numeric, BigInteger
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=True)
    phone = Column(String(50))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    practice_area = Column(String(255))
    message = Column(Text, nullable=False)
    preferred_date = Column(Date, nullable=True)
    preferred_time = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    attorney_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Case(Base):
    __tablename__ = "cases"

    id = Column(BigInteger, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, nullable=False)
    case_name = Column(String(255), nullable=False)
    case_type = Column(String(255))
    description = Column(Text)
    status = Column(String(50), default="open")
    client_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    attorney_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    court = Column(String(255))
    judge = Column(String(255))
    filed_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class CaseHearing(Base):
    __tablename__ = "case_hearings"

    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    hearing_date = Column(Date, nullable=False)
    hearing_time = Column(String(50))
    court = Column(String(255))
    judge = Column(String(255))
    status = Column(String(50), default="scheduled")
    notes = Column(Text)
    rescheduled_from_id = Column(BigInteger, ForeignKey("case_hearings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    file_url = Column(Text)
    file_type = Column(String(100))
    file_size = Column(BigInteger)
    case_id = Column(BigInteger, ForeignKey("cases.id"), nullable=True)
    uploaded_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    description = Column(Text)
    is_confidential = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, index=True)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    recipient_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    case_id = Column(BigInteger, ForeignKey("cases.id"), nullable=True)
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    parent_id = Column(BigInteger, ForeignKey("messages.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(String(100))
    title = Column(String(500), nullable=False)
    body = Column(Text)
    is_read = Column(Boolean, default=False)
    link = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    client_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    case_id = Column(BigInteger, ForeignKey("cases.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="unpaid")
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(255))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(BigInteger, nullable=True)
    description = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
