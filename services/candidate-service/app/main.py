# services/candidate-service/app/main.py
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from services.common import settings, configure_logging, register_exception_handlers
from services.common.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.adapter.db.database import engine, Base
from app.delivery.http.router import router

# Initialize structured logging
configure_logging()
logger = logging.getLogger(__name__)

# Auto-create tables (for local dev helper)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.warning(f"Database offline or tables checked on application connect: {e}")

# Base application with configuration settings loaded
app = FastAPI(
    title="HR-Copilot Candidate & Job Service",
    description="Microservice responsible for Candidate profile parsing, job postings, and interview session initialization.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Centralized exception handlers registration
register_exception_handlers(app)

# Production security & rate-limiting middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route attachment
app.include_router(router)


# System Health and Probe Endpoints
@app.get("/health", tags=["System"])
@app.get("/live", tags=["System"])
def liveness_check():
    """
    Liveness probe ensuring the web server process is running.
    """
    return {"status": "healthy", "service": "candidate-service"}


@app.get("/ready", tags=["System"])
def readiness_check():
    """
    Readiness probe validating underlying resource availability (PostgreSQL).
    """
    try:
        from app.adapter.db.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        logger.error(f"Readiness check failed: Database unreachable. Exception: {e}")
        raise HTTPException(status_code=503, detail="Postgres database is unreachable")
        
    return {"status": "ready", "service": "candidate-service"}


@app.get("/version", tags=["System"])
def version():
    """
    Returns API version.
    """
    return {"version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
