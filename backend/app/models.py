import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime,
    Enum, ForeignKey, Text, DECIMAL
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from app.database import Base


def new_uuid():
    return str(uuid.uuid4())


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    original_name = Column(String(512), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    total_rows = Column(Integer, default=0)
    status = Column(
        Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED"),
        default="PENDING",
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    storage_path = Column(String(1024), nullable=True)
    checksum_md5 = Column(String(32), nullable=True)

    chunks = relationship("FileChunk", back_populates="session", cascade="all, delete")
    transactions = relationship("Transaction", back_populates="session", cascade="all, delete")
    summary = relationship("ValidationSummary", back_populates="session", uselist=False, cascade="all, delete")
    output_files = relationship("OutputFile", back_populates="session", cascade="all, delete")
    audit_events = relationship("AuditEvent", back_populates="session", cascade="all, delete")


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    row_start = Column(Integer, nullable=False)
    row_end = Column(Integer, nullable=False)
    status = Column(
        Enum("PENDING", "PROCESSING", "DONE", "FAILED"),
        default="PENDING",
    )
    celery_task_id = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True)

    session = relationship("UploadSession", back_populates="chunks")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    is_valid = Column(Boolean, nullable=True)
    is_fixed = Column(Boolean, default=False)
    fixed_data = Column(JSON, nullable=True)

    session = relationship("UploadSession", back_populates="transactions")
    errors = relationship("ValidationError", back_populates="transaction", cascade="all, delete")


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(BigInteger, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), nullable=False)
    field_name = Column(String(128), nullable=True)
    error_code = Column(String(64), nullable=False)
    error_category = Column(
        Enum("PHONE", "DATE", "EMAIL", "PAYMENT", "PRODUCT", "DUPLICATE", "MISSING", "CURRENCY", "INTEGRITY"),
        nullable=False,
    )
    severity = Column(Enum("ERROR", "WARNING"), default="ERROR")
    raw_value = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    fix_suggestion = Column(Text, nullable=True)
    fix_action = Column(String(64), nullable=True)
    fix_accepted = Column(Boolean, default=False)

    transaction = relationship("Transaction", back_populates="errors")


class ValidationSummary(Base):
    __tablename__ = "validation_summaries"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    fixed_rows = Column(Integer, default=0)
    health_score = Column(DECIMAL(5, 2), nullable=True)
    error_breakdown = Column(JSON, nullable=True)
    country_breakdown = Column(JSON, nullable=True)
    top_failures = Column(JSON, nullable=True)
    ai_insights = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UploadSession", back_populates="summary")


class OutputFile(Base):
    __tablename__ = "output_files"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(
        Enum("CLEANED_CSV", "INVALID_CSV", "VALIDATION_REPORT_PDF", "ERROR_EXPLANATION_CSV", "AUDIT_LOG_JSON"),
        nullable=False,
    )
    storage_path = Column(String(1024), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UploadSession", back_populates="output_files")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(64), nullable=False)
    event_data = Column(JSON, nullable=True)
    actor = Column(String(128), default="system")
    occurred_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UploadSession", back_populates="audit_events")
