import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, employees, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown logic if needed on shutdown
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Enterprise Employee Management System API with JWT Authentication, "
        "Role-based CRUD, Prometheus Metrics, and Kubernetes Health Probes."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ---------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Prometheus Instrumentation (/metrics)
# ---------------------------------------------------------
Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
    tags=["Monitoring"],
)

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(health.router)

# ---------------------------------------------------------
# Static Dashboard & Frontend Web UI
# ---------------------------------------------------------
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the rich interactive frontend dashboard if present, otherwise returns service info."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        content={
            "service": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
        }
    )
