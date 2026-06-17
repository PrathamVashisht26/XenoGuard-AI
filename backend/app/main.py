import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers import upload, sessions, fixes, downloads, events

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="XenoGuard AI",
    description="Intelligent Global Transaction Validation & Recovery Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "trace": traceback.format_exc()},
    )

app.include_router(upload.router, prefix="/v1", tags=["Upload"])
app.include_router(sessions.router, prefix="/v1", tags=["Sessions"])
app.include_router(fixes.router, prefix="/v1", tags=["Fixes"])
app.include_router(downloads.router, prefix="/v1", tags=["Downloads"])
app.include_router(events.router, prefix="/v1", tags=["Events"])


@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "service": "XenoGuard AI"}


@app.get("/debug")
def debug():
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as e:
        db_ok = str(e)
    try:
        from app.workers.celery_app import celery_app
        celery_ok = str(celery_app.control.inspect(timeout=2).ping() or "no workers")
    except Exception as e:
        celery_ok = str(e)
    return {
        "database": db_ok,
        "celery": celery_ok,
        "cors_origins": settings.CORS_ORIGINS,
        "storage_root": settings.STORAGE_ROOT,
    }
