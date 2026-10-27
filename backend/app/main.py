from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*"
            )
        return response

from backend.app.config import settings
from backend.app.api import api_router
from backend.app.auth.routes_auth import router as auth_router
from backend.app.database import engine, Base, SessionLocal
from backend.app.api.routes_buses import ensure_bus_columns
from backend.app.models.plan import ensure_plan_columns
from backend.app.models.institution import seed_default_institutions
import backend.app.models  # noqa: F401 — registers all models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifespan handler (Resolves M-11 and M-12).
    Ensures all database tables, columns, and seed institutions are initialized
    cleanly inside the server lifecycle rather than as side-effects at import time.
    """
    # 1. Ensure all database tables exist
    Base.metadata.create_all(bind=engine)
    # 2. Ensure dynamic columns exist on SQLite
    ensure_bus_columns()
    ensure_plan_columns()
    # 3. Seed default institutions idempotently
    with SessionLocal() as init_db:
        seed_default_institutions(init_db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Intelligent Demand-Aware Bus Fleet Allocation & Capacitated Routing Platform "
        "for VSB Engineering College, Karudayampalayam, Karur."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS — restricted to declared origins (never wildcard in production)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Authentication router (login → JWT token) ──────────────────────────────
app.include_router(auth_router, prefix=settings.API_PREFIX)

# ── Core API router (all domain endpoints) ────────────────────────────────
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["System Root"])
def root_endpoint():
    """System welcome and operational metadata."""
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX,
        "status": "OPERATIONAL",
    }


@app.get("/api/health", tags=["System Root"])
def health_check():
    """Operational health status verifying DB connection and fleet parameters."""
    from sqlalchemy import text

    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "HEALTHY" if db_connected else "DEGRADED",
        "database_connected": db_connected,
        "total_fleet_size": settings.TOTAL_FLEET_SIZE,
        "bus_capacity": settings.DEFAULT_BUS_CAPACITY,
        "target_arrival_time": settings.FIRST_CLASS_ARRIVAL_TIME,
        "college_hub": settings.COLLEGE_NAME,
        "osrm_url": settings.OSRM_BASE_URL,
        "haversine_fallback_enabled": settings.ENABLE_OFFLINE_HAVERSINE_FALLBACK,
    }

