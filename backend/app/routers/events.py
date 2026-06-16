import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import func

from app.database import SessionLocal
from app.models import UploadSession, FileChunk

router = APIRouter()


@router.get("/events/{session_id}")
async def session_events(session_id: str):

    async def event_generator():
        while True:
            db = SessionLocal()
            try:
                session = db.query(UploadSession).filter_by(id=session_id).first()
                if not session:
                    data = json.dumps({"error": "Session not found"})
                    yield f"data: {data}\n\n"
                    break

                chunks = db.query(FileChunk).filter_by(session_id=session_id).all()
                total_chunks = len(chunks)
                done_chunks = sum(1 for c in chunks if c.status == "DONE")
                failed_chunks = sum(1 for c in chunks if c.status == "FAILED")

                payload = {
                    "session_id": session_id,
                    "status": session.status,
                    "total_rows": session.total_rows,
                    "total_chunks": total_chunks,
                    "done_chunks": done_chunks,
                    "failed_chunks": failed_chunks,
                    "progress_pct": round(done_chunks / total_chunks * 100 if total_chunks > 0 else 0),
                }
                yield f"data: {json.dumps(payload)}\n\n"

                if session.status in ("COMPLETED", "FAILED"):
                    break
            finally:
                db.close()

            await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
