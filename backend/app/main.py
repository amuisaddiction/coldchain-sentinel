"""ColdChain Sentinel - Master FastAPI Application Entrypoint."""

import sys
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-verified shipment acceptance and payment assurance API for cold chain pharmaceuticals.",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "tagline": "Every Degree Matters. Every Payment Must Be Earned.",
        "status": "operational",
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.APP_DEBUG else "disabled",
    }


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Comprehensive system health and runtime environment verification."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.VERSION,
        "python_runtime": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "database_connected": db_ok,
        "database_url_dialect": settings.DATABASE_URL.split(":")[0],
        "storage_backend": settings.STORAGE_BACKEND,
        "paypal_mode": settings.PAYPAL_MODE,
        "gemini_enabled": bool(settings.GEMINI_API_KEY),
    }
