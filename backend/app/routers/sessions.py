import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UploadSession, Transaction, ValidationError, ValidationSummary, FileChunk, AuditEvent

router = APIRouter()


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    chunks = db.query(FileChunk).filter_by(session_id=session_id).all()
    done_chunks = sum(1 for c in chunks if c.status == "DONE")
    return {
        "session_id": session.id,
        "original_name": session.original_name,
        "file_size_bytes": session.file_size_bytes,
        "total_rows": session.total_rows,
        "status": session.status,
        "uploaded_at": session.uploaded_at.isoformat() if session.uploaded_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "total_chunks": len(chunks),
        "done_chunks": done_chunks,
    }


@router.get("/sessions/{session_id}/preview")
def get_preview(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter_by(id=session_id).first()
    if not session or not session.storage_path:
        raise HTTPException(status_code=404, detail="Session or file not found.")
    path = Path(session.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Original file not found.")
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 100:
                break
            rows.append(dict(row))
    headers = list(rows[0].keys()) if rows else []
    return {"headers": headers, "rows": rows, "count": len(rows)}


@router.get("/sessions/{session_id}/summary")
def get_summary(session_id: str, db: Session = Depends(get_db)):
    summary = db.query(ValidationSummary).filter_by(session_id=session_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not yet available. Processing may still be running.")
    return {
        "session_id": session_id,
        "health_score": float(summary.health_score or 0),
        "total_rows": summary.total_rows,
        "valid_rows": summary.valid_rows,
        "invalid_rows": summary.invalid_rows,
        "fixed_rows": summary.fixed_rows,
        "error_breakdown": summary.error_breakdown or {},
        "country_breakdown": summary.country_breakdown or {},
        "top_failures": summary.top_failures or [],
        "ai_insights": summary.ai_insights or [],
        "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
    }


@router.get("/sessions/{session_id}/transactions")
def get_transactions(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    filter: str = Query("all"),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).filter_by(session_id=session_id)
    if filter == "valid":
        q = q.filter(Transaction.is_valid == True)
    elif filter == "invalid":
        q = q.filter(Transaction.is_valid == False)
    total = q.count()
    txns = q.order_by(Transaction.row_number).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "rows": [
            {
                "id": t.id,
                "row_number": t.row_number,
                "is_valid": t.is_valid,
                "is_fixed": t.is_fixed,
                "data": t.fixed_data if t.is_fixed else t.raw_data,
                "error_count": db.query(ValidationError).filter_by(transaction_id=t.id).count(),
            }
            for t in txns
        ],
    }


@router.get("/sessions/{session_id}/errors")
def get_errors(
    session_id: str,
    transaction_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(ValidationError).filter_by(session_id=session_id)
    if transaction_id:
        q = q.filter(ValidationError.transaction_id == transaction_id)
    total = q.count()
    errs = q.order_by(ValidationError.id).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "errors": [
            {
                "id": e.id,
                "transaction_id": e.transaction_id,
                "field_name": e.field_name,
                "error_code": e.error_code,
                "error_category": e.error_category,
                "severity": e.severity,
                "raw_value": e.raw_value,
                "explanation": e.explanation,
                "fix_suggestion": e.fix_suggestion,
                "fix_action": e.fix_action,
                "fix_accepted": e.fix_accepted,
            }
            for e in errs
        ],
    }


@router.get("/sessions/{session_id}/insights")
def get_insights(session_id: str, db: Session = Depends(get_db)):
    summary = db.query(ValidationSummary).filter_by(session_id=session_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Insights not yet generated.")
    return {"insights": summary.ai_insights or []}


@router.get("/sessions/{session_id}/audit")
def get_audit(session_id: str, db: Session = Depends(get_db)):
    events = db.query(AuditEvent).filter_by(session_id=session_id).order_by(AuditEvent.occurred_at).all()
    return {
        "events": [
            {
                "event_type": e.event_type,
                "actor": e.actor,
                "occurred_at": e.occurred_at.isoformat(),
                "event_data": e.event_data,
            }
            for e in events
        ]
    }
