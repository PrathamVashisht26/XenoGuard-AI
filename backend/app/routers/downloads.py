from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OutputFile, UploadSession

router = APIRouter()

FILE_TYPE_DISPLAY = {
    "CLEANED_CSV": "cleaned_dataset.csv",
    "INVALID_CSV": "invalid_records.csv",
    "VALIDATION_REPORT_PDF": "validation_report.pdf",
    "ERROR_EXPLANATION_CSV": "error_explanations.csv",
    "AUDIT_LOG_JSON": "audit_log.json",
}

MEDIA_TYPES = {
    "CLEANED_CSV": "text/csv",
    "INVALID_CSV": "text/csv",
    "VALIDATION_REPORT_PDF": "application/pdf",
    "ERROR_EXPLANATION_CSV": "text/csv",
    "AUDIT_LOG_JSON": "application/json",
}


@router.get("/sessions/{session_id}/downloads")
def list_downloads(session_id: str, db: Session = Depends(get_db)):
    files = db.query(OutputFile).filter_by(session_id=session_id).all()
    return {
        "files": [
            {
                "id": f.id,
                "file_type": f.file_type,
                "display_name": FILE_TYPE_DISPLAY.get(f.file_type, f.file_type),
                "file_size_bytes": f.file_size_bytes,
                "generated_at": f.generated_at.isoformat() if f.generated_at else None,
            }
            for f in files
        ]
    }


@router.get("/downloads/{file_id}")
def download_file(file_id: str, db: Session = Depends(get_db)):
    output_file = db.query(OutputFile).filter_by(id=file_id).first()
    if not output_file:
        raise HTTPException(status_code=404, detail="File not found.")
    path = Path(output_file.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")
    return FileResponse(
        path=str(path),
        media_type=MEDIA_TYPES.get(output_file.file_type, "application/octet-stream"),
        filename=FILE_TYPE_DISPLAY.get(output_file.file_type, path.name),
    )
