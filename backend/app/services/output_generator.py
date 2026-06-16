import csv
import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Transaction, ValidationError, OutputFile, AuditEvent, ValidationSummary
)


class OutputGenerator:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db = SessionLocal()
        self.out_dir = Path(settings.STORAGE_ROOT) / session_id / "outputs"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        try:
            self._gen_cleaned_csv()
            self._gen_invalid_csv()
            self._gen_error_explanation_csv()
            self._gen_audit_log()
            self._gen_pdf_report()
        finally:
            self.db.close()

    def _save_output_file(self, path: Path, file_type: str):
        size = path.stat().st_size
        existing = self.db.query(OutputFile).filter_by(
            session_id=self.session_id, file_type=file_type
        ).first()
        if existing:
            existing.storage_path = str(path)
            existing.file_size_bytes = size
            existing.generated_at = datetime.utcnow()
        else:
            self.db.add(OutputFile(
                id=str(uuid.uuid4()),
                session_id=self.session_id,
                file_type=file_type,
                storage_path=str(path),
                file_size_bytes=size,
            ))
        self.db.commit()

    def _gen_cleaned_csv(self):
        path = self.out_dir / "cleaned_dataset.csv"
        txns = self.db.query(Transaction).filter_by(
            session_id=self.session_id, is_valid=True
        ).order_by(Transaction.row_number).all()
        fixed_txns = self.db.query(Transaction).filter_by(
            session_id=self.session_id, is_fixed=True
        ).order_by(Transaction.row_number).all()

        all_rows = []
        seen_ids = set()
        for txn in txns + fixed_txns:
            if txn.id not in seen_ids:
                data = txn.fixed_data if txn.is_fixed else txn.raw_data
                all_rows.append(self._sanitize_row(data))
                seen_ids.add(txn.id)

        self._write_csv(path, all_rows)
        self._save_output_file(path, "CLEANED_CSV")

    def _gen_invalid_csv(self):
        path = self.out_dir / "invalid_records.csv"
        txns = self.db.query(Transaction).filter_by(
            session_id=self.session_id, is_valid=False, is_fixed=False
        ).order_by(Transaction.row_number).all()
        rows = [self._sanitize_row(t.raw_data) for t in txns]
        self._write_csv(path, rows)
        self._save_output_file(path, "INVALID_CSV")

    def _gen_error_explanation_csv(self):
        path = self.out_dir / "error_explanations.csv"
        errors = self.db.query(ValidationError).filter_by(
            session_id=self.session_id
        ).order_by(ValidationError.transaction_id).all()

        rows = []
        for err in errors:
            txn = self.db.query(Transaction).filter_by(id=err.transaction_id).first()
            rows.append({
                "row_number": txn.row_number if txn else "",
                "order_id": txn.raw_data.get("order_id", "") if txn else "",
                "field": err.field_name or "",
                "error_code": err.error_code,
                "category": err.error_category,
                "severity": err.severity,
                "raw_value": err.raw_value or "",
                "explanation": err.explanation or "",
                "fix_suggestion": err.fix_suggestion or "",
                "fix_accepted": err.fix_accepted,
            })
        self._write_csv(path, rows)
        self._save_output_file(path, "ERROR_EXPLANATION_CSV")

    def _gen_audit_log(self):
        path = self.out_dir / "audit_log.json"
        events = self.db.query(AuditEvent).filter_by(
            session_id=self.session_id
        ).order_by(AuditEvent.occurred_at).all()
        data = [
            {
                "event_type": e.event_type,
                "actor": e.actor,
                "occurred_at": e.occurred_at.isoformat(),
                "event_data": e.event_data,
            }
            for e in events
        ]
        path.write_text(json.dumps(data, indent=2, default=str))
        self._save_output_file(path, "AUDIT_LOG_JSON")

    def _gen_pdf_report(self):
        from app.services.pdf_generator import generate_pdf_report
        path = self.out_dir / "validation_report.pdf"
        summary = self.db.query(ValidationSummary).filter_by(
            session_id=self.session_id
        ).first()
        if summary:
            generate_pdf_report(path, summary)
            self._save_output_file(path, "VALIDATION_REPORT_PDF")

    @staticmethod
    def _sanitize_row(data: dict) -> dict:
        safe = {}
        dangerous_starts = ("=", "+", "-", "@", "\t", "\r")
        for k, v in data.items():
            s = str(v)
            if s.startswith(dangerous_starts):
                s = "'" + s
            safe[k] = s
        return safe

    @staticmethod
    def _write_csv(path: Path, rows: list[dict]):
        if not rows:
            path.write_text("")
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
