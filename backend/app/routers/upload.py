import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import UploadSession, AuditEvent

router = APIRouter()

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
UPLOAD_ROOT = Path(settings.STORAGE_ROOT)


def _run_processing(session_id: str, file_path: str):
    """Run processing synchronously in a background thread (no Celery needed)."""
    try:
        from app.workers.tasks import split_and_enqueue
        # Try Celery first
        split_and_enqueue.delay(session_id, file_path)
    except Exception:
        # Fallback: run the core logic directly without Celery
        try:
            from app.workers.tasks import _run_full_pipeline
            _run_full_pipeline(session_id, file_path)
        except Exception as e:
            # Log but don't crash — session will stay PENDING
            import traceback
            print(f"[ERROR] Processing failed for {session_id}: {e}")
            print(traceback.format_exc())


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    if background_tasks is None:
        background_tasks = BackgroundTasks()
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    checksum = hashlib.md5(content).hexdigest()
    session_id = str(uuid.uuid4())

    session_dir = UPLOAD_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    file_path = session_dir / "original.csv"
    file_path.write_bytes(content)

    db_session = UploadSession(
        id=session_id,
        original_name=file.filename,
        file_size_bytes=len(content),
        status="PENDING",
        storage_path=str(file_path),
        checksum_md5=checksum,
    )
    db.add(db_session)

    db.add(AuditEvent(
        session_id=session_id,
        event_type="FILE_UPLOADED",
        event_data={"filename": file.filename, "size_bytes": len(content)},
    ))
    db.commit()

    # Run in background thread — no Redis/Celery needed
    background_tasks.add_task(_run_processing, session_id, str(file_path))

    return {
        "session_id": session_id,
        "status": "PENDING",
        "filename": file.filename,
        "size_bytes": len(content),
        "message": "Upload successful. Processing started.",
    }
