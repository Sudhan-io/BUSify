from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api import api_router
from backend.app.auth.routes_auth import router as auth_router
from backend.app.database import engine, Base

# Ensure all tables are created on startup (incl. student_attendance)
import backend.app.models  # noqa: F401 — registers all models with Base.metadata
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Intelligent Demand-Aware Bus Fleet Allocation & Capacitated Routing Platform "
        "for VSB Engineering College, Karudayampalayam, Karur."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — restricted to declared origins (never wildcard in production)
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

