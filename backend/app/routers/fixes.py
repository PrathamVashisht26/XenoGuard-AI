from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import ValidationError, Transaction, AuditEvent
from app.engine.fix.fix_engine import fix_engine

router = APIRouter()


@router.patch("/fixes/{error_id}/accept")
def accept_fix(error_id: int, db: Session = Depends(get_db)):
    err = db.query(ValidationError).filter_by(id=error_id).first()
    if not err:
        raise HTTPException(status_code=404, detail="Error not found.")
    if not err.fix_action:
        raise HTTPException(status_code=400, detail="No automatic fix available for this error.")
    if err.fix_accepted:
        return {"message": "Fix already accepted.", "error_id": error_id}

    txn = db.query(Transaction).filter_by(id=err.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    current_data = txn.fixed_data if txn.is_fixed else txn.raw_data
    fixed_data = fix_engine.apply_fix(err.fix_action, current_data, err.field_name or "")

    if fixed_data is not None:
        txn.fixed_data = fixed_data
        txn.is_fixed = True
        txn.is_valid = True
    else:
        txn.is_valid = False
        txn.is_fixed = True

    err.fix_accepted = True

    db.add(AuditEvent(
        session_id=err.session_id,
        event_type="FIX_ACCEPTED",
        event_data={
            "error_id": error_id,
            "error_code": err.error_code,
            "transaction_id": err.transaction_id,
            "fix_action": err.fix_action,
        },
        actor="user",
    ))
    db.commit()

    return {"message": "Fix accepted and applied.", "error_id": error_id, "fixed_data": txn.fixed_data}


@router.post("/sessions/{session_id}/fixes/accept-all")
def accept_all_fixes(session_id: str, db: Session = Depends(get_db)):
    errors = db.query(ValidationError).filter_by(
        session_id=session_id, fix_accepted=False
    ).filter(ValidationError.fix_action.isnot(None)).all()

    accepted_count = 0
    for err in errors:
        txn = db.query(Transaction).filter_by(id=err.transaction_id).first()
        if not txn:
            continue
        current_data = txn.fixed_data if txn.is_fixed else txn.raw_data
        fixed_data = fix_engine.apply_fix(err.fix_action, current_data, err.field_name or "")
        if fixed_data is not None:
            txn.fixed_data = fixed_data
            txn.is_fixed = True
            txn.is_valid = True
        err.fix_accepted = True
        accepted_count += 1

    db.add(AuditEvent(
        session_id=session_id,
        event_type="BULK_FIX_ACCEPTED",
        event_data={"fixes_applied": accepted_count},
        actor="user",
    ))
    db.commit()

    return {"message": f"{accepted_count} fixes applied.", "accepted_count": accepted_count}
