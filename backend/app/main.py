from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(upload.router, prefix="/v1", tags=["Upload"])
app.include_router(sessions.router, prefix="/v1", tags=["Sessions"])
app.include_router(fixes.router, prefix="/v1", tags=["Fixes"])
app.include_router(downloads.router, prefix="/v1", tags=["Downloads"])
app.include_router(events.router, prefix="/v1", tags=["Events"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "XenoGuard AI"}
