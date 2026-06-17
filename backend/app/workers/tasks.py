import os
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import pandas as pd

from app.workers.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models import (
    UploadSession, FileChunk, Transaction,
    ValidationError as DBError, ValidationSummary, OutputFile, AuditEvent
)
from app.engine.validation import validate_row
from app.engine.explanation.nlg_engine import explain_error
from app.engine.insight.insight_engine import generate_insights


def _get_db():
    return SessionLocal()


def _run_full_pipeline(session_id: str, file_path: str):
    """Run the full validation pipeline synchronously — no Celery required."""
    import uuid as _uuid
    from datetime import datetime as _dt
    from collections import defaultdict as _dd
    from sqlalchemy import func

    db = _get_db()
    try:
        session = db.query(UploadSession).filter_by(id=session_id).first()
        session.status = "PROCESSING"
        db.commit()

        chunk_size = settings.CHUNK_SIZE_ROWS
        df_iter = pd.read_csv(file_path, chunksize=chunk_size, dtype=str)
        chunk_dir = Path(file_path).parent / session_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        total_rows = 0
        context = {"seen_order_ids": set()}

        for idx, chunk_df in enumerate(df_iter):
            chunk_df = chunk_df.fillna("")
            row_start = idx * chunk_size
            total_rows += len(chunk_df)

            for local_idx, row in enumerate(chunk_df.to_dict("records")):
                abs_row_number = row_start + local_idx + 2
                errors = validate_row(row, context)
                is_valid = len(errors) == 0

                txn = Transaction(
                    session_id=session_id,
                    row_number=abs_row_number,
                    raw_data=row,
                    is_valid=is_valid,
                )
                db.add(txn)
                db.flush()

                for err in errors:
                    explanation, suggestion, fix_action = explain_error(err)
                    db_err = DBError(
                        transaction_id=txn.id,
                        session_id=session_id,
                        field_name=err.field_name,
                        error_code=err.error_code,
                        error_category=err.error_category,
                        severity=err.severity,
                        raw_value=err.raw_value,
                        explanation=explanation,
                        fix_suggestion=suggestion,
                        fix_action=fix_action,
                        fix_accepted=False,
                    )
                    db.add(db_err)

            db.commit()

        session.total_rows = total_rows
        db.commit()

        # Aggregate
        total = db.query(func.count(Transaction.id)).filter_by(session_id=session_id).scalar() or 0
        valid = db.query(func.count(Transaction.id)).filter_by(session_id=session_id, is_valid=True).scalar() or 0
        invalid = total - valid
        health_score = round((valid / total * 100) if total > 0 else 0.0, 2)

        cat_counts = db.query(DBError.error_category, func.count(DBError.id))\
            .filter(DBError.session_id == session_id)\
            .group_by(DBError.error_category).all()
        error_breakdown = {cat: cnt for cat, cnt in cat_counts}

        country_breakdown = _dd(int)
        code_counts = db.query(DBError.error_code, func.count(DBError.id))\
            .filter(DBError.session_id == session_id)\
            .group_by(DBError.error_code)\
            .order_by(func.count(DBError.id).desc())\
            .limit(10).all()
        total_err = sum(c for _, c in code_counts) or 1
        top_failures = [
            {"code": code, "count": cnt, "pct": round(cnt / total_err * 100, 1)}
            for code, cnt in code_counts
        ]

        ai_insights = generate_insights(
            health_score=health_score,
            total_rows=total,
            error_breakdown=error_breakdown,
            country_breakdown=dict(country_breakdown),
            top_failures=top_failures,
        )

        existing = db.query(ValidationSummary).filter_by(session_id=session_id).first()
        if existing:
            summary = existing
        else:
            summary = ValidationSummary(id=str(_uuid.uuid4()), session_id=session_id)
            db.add(summary)

        summary.total_rows = total
        summary.valid_rows = valid
        summary.invalid_rows = invalid
        summary.health_score = health_score
        summary.error_breakdown = error_breakdown
        summary.country_breakdown = dict(country_breakdown)
        summary.top_failures = top_failures
        summary.ai_insights = ai_insights
        summary.generated_at = _dt.utcnow()

        session.status = "COMPLETED"
        session.completed_at = _dt.utcnow()

        db.add(AuditEvent(
            session_id=session_id,
            event_type="VALIDATION_COMPLETED",
            event_data={"total": total, "valid": valid, "invalid": invalid, "score": health_score},
        ))
        db.commit()

        # Generate output files
        from app.services.output_generator import OutputGenerator
        gen = OutputGenerator(session_id)
        gen.generate_all()

    except Exception as exc:
        import traceback
        print(f"[ERROR] _run_full_pipeline failed: {exc}")
        print(traceback.format_exc())
        try:
            session = db.query(UploadSession).filter_by(id=session_id).first()
            if session:
                session.status = "FAILED"
                db.commit()
        except Exception:
            pass
        raise exc
    finally:
        db.close()



@celery_app.task(bind=True, name="xenoguard.split_and_enqueue")
def split_and_enqueue(self, session_id: str, file_path: str):
    db = _get_db()
    try:
        session = db.query(UploadSession).filter_by(id=session_id).first()
        session.status = "PROCESSING"
        db.commit()

        chunk_size = settings.CHUNK_SIZE_ROWS
        chunks_data = []

        df_iter = pd.read_csv(file_path, chunksize=chunk_size, dtype=str)
        chunk_dir = Path(file_path).parent / session_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        total_rows = 0
        for idx, chunk_df in enumerate(df_iter):
            chunk_df = chunk_df.fillna("")
            row_start = idx * chunk_size
            row_end = row_start + len(chunk_df) - 1
            total_rows += len(chunk_df)

            chunk_path = str(chunk_dir / f"chunk_{idx}.csv")
            chunk_df.to_csv(chunk_path, index=False)

            chunk_id = str(uuid.uuid4())
            db_chunk = FileChunk(
                id=chunk_id,
                session_id=session_id,
                chunk_index=idx,
                row_start=row_start,
                row_end=row_end,
                status="PENDING",
            )
            db.add(db_chunk)
            db.commit()

            chunks_data.append({"chunk_id": chunk_id, "chunk_path": chunk_path, "row_start": row_start})

        session.total_rows = total_rows
        db.commit()

        from celery import group, chain as celery_chain
        validation_group = group(
            validate_chunk.s(session_id, c["chunk_id"], c["chunk_path"], c["row_start"])
            for c in chunks_data
        )
        workflow = celery_chain(
            validation_group,
            aggregate_results.s(session_id),
            generate_output_files.s(session_id),
        )
        workflow.delay()

    except Exception as exc:
        session = db.query(UploadSession).filter_by(id=session_id).first()
        if session:
            session.status = "FAILED"
            db.commit()
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="xenoguard.validate_chunk")
def validate_chunk(self, session_id: str, chunk_id: str, chunk_path: str, row_offset: int):
    db = _get_db()
    try:
        chunk_rec = db.query(FileChunk).filter_by(id=chunk_id).first()
        chunk_rec.status = "PROCESSING"
        chunk_rec.celery_task_id = self.request.id
        db.commit()

        df = pd.read_csv(chunk_path, dtype=str).fillna("")
        context = {"seen_order_ids": set()}

        for local_idx, row in enumerate(df.to_dict("records")):
            abs_row_number = row_offset + local_idx + 2
            errors = validate_row(row, context)
            is_valid = len(errors) == 0

            txn = Transaction(
                session_id=session_id,
                row_number=abs_row_number,
                raw_data=row,
                is_valid=is_valid,
            )
            db.add(txn)
            db.flush()

            for err in errors:
                explanation, suggestion, fix_action = explain_error(err)
                db_err = DBError(
                    transaction_id=txn.id,
                    session_id=session_id,
                    field_name=err.field_name,
                    error_code=err.error_code,
                    error_category=err.error_category,
                    severity=err.severity,
                    raw_value=err.raw_value,
                    explanation=explanation,
                    fix_suggestion=suggestion,
                    fix_action=fix_action,
                    fix_accepted=False,
                )
                db.add(db_err)

        db.commit()
        chunk_rec.status = "DONE"
        chunk_rec.processed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        chunk_rec = db.query(FileChunk).filter_by(id=chunk_id).first()
        if chunk_rec:
            chunk_rec.status = "FAILED"
            db.commit()
        raise exc
    finally:
        db.close()


@celery_app.task(name="xenoguard.aggregate_results")
def aggregate_results(chunk_results, session_id: str):
    db = _get_db()
    try:
        from sqlalchemy import func
        from app.models import Transaction as Txn, ValidationError as VErr

        total = db.query(func.count(Txn.id)).filter_by(session_id=session_id).scalar() or 0
        valid = db.query(func.count(Txn.id)).filter_by(session_id=session_id, is_valid=True).scalar() or 0
        invalid = total - valid

        health_score = round((valid / total * 100) if total > 0 else 0.0, 2)

        cat_counts = db.query(VErr.error_category, func.count(VErr.id))\
            .filter(VErr.session_id == session_id)\
            .group_by(VErr.error_category).all()
        error_breakdown = {cat: cnt for cat, cnt in cat_counts}

        country_breakdown = defaultdict(int)
        errors_with_txn = db.query(VErr, Txn)\
            .join(Txn, VErr.transaction_id == Txn.id)\
            .filter(VErr.session_id == session_id)\
            .filter(VErr.error_category == "PHONE").all()
        for err, txn in errors_with_txn:
            cc = txn.raw_data.get("country_code", "UNKNOWN")
            country_breakdown[cc] += 1

        code_counts = db.query(VErr.error_code, func.count(VErr.id))\
            .filter(VErr.session_id == session_id)\
            .group_by(VErr.error_code)\
            .order_by(func.count(VErr.id).desc())\
            .limit(10).all()
        total_err = sum(c for _, c in code_counts) or 1
        top_failures = [
            {"code": code, "count": cnt, "pct": round(cnt / total_err * 100, 1)}
            for code, cnt in code_counts
        ]

        ai_insights = generate_insights(
            health_score=health_score,
            total_rows=total,
            error_breakdown=error_breakdown,
            country_breakdown=dict(country_breakdown),
            top_failures=top_failures,
        )

        existing = db.query(ValidationSummary).filter_by(session_id=session_id).first()
        if existing:
            summary = existing
        else:
            summary = ValidationSummary(id=str(uuid.uuid4()), session_id=session_id)
            db.add(summary)

        summary.total_rows = total
        summary.valid_rows = valid
        summary.invalid_rows = invalid
        summary.health_score = health_score
        summary.error_breakdown = error_breakdown
        summary.country_breakdown = dict(country_breakdown)
        summary.top_failures = top_failures
        summary.ai_insights = ai_insights
        summary.generated_at = datetime.utcnow()

        session = db.query(UploadSession).filter_by(id=session_id).first()
        session.status = "COMPLETED"
        session.completed_at = datetime.utcnow()

        db.add(AuditEvent(
            session_id=session_id,
            event_type="VALIDATION_COMPLETED",
            event_data={"total": total, "valid": valid, "invalid": invalid, "score": health_score},
        ))
        db.commit()

    finally:
        db.close()


@celery_app.task(name="xenoguard.generate_output_files")
def generate_output_files(_, session_id: str):
    from app.services.output_generator import OutputGenerator
    gen = OutputGenerator(session_id)
    gen.generate_all()
