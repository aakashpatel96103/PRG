from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.database import check_db_connection

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("", summary="Kubernetes Liveness Probe")
@router.get("/live", summary="Liveness check alias")
def liveness():
    """Liveness probe: verifies that the application process is running."""
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
    }


@router.get("/ready", summary="Kubernetes Readiness Probe")
def readiness():
    """Readiness probe: validates database connectivity before accepting ingress traffic."""
    db_ok = check_db_connection()
    now_iso = datetime.now(UTC).isoformat()
    if db_ok:
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": now_iso,
        }
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "database": "disconnected",
            "timestamp": now_iso,
        },
    )
