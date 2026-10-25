import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "BUSify Transit Optimization Platform"
    VERSION: str = "0.2.0"
    API_PREFIX: str = "/api"

    # ─── Database ─────────────────────────────────────────────────────────────
    # Override via DATABASE_URL env var. Default is local SQLite for dev only.
    DATABASE_URL: str = Field(
        default="sqlite:///./busify.db",
        description="SQLAlchemy connection string. Use postgresql:// in production.",
    )

    # ─── Security (REQUIRED — no safe defaults) ────────────────────────────────
    # Generate: python -c "import secrets; print(secrets.token_hex(64))"
    JWT_SECRET: str = Field(
        ...,
        description="HS256 signing secret for JWT bearer tokens. Must be 64+ hex chars.",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8-hour transport officer shift

    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    STUDENT_HASH_SALT: str = Field(
        ...,
        description="HMAC salt for student ID anonymisation. Never commit to source control.",
    )

    TRANSPORT_OFFICER_PASSWORD: str = Field(
        default="vsb_transport_dev_2026",
        description="Password for transport officer login (set in .env)",
    )
    ADMIN_PASSWORD: str = Field(
        default="vsb_admin_dev_2026",
        description="Password for system administrator login (set in .env)",
    )

    # ─── Campus Depot Geolocation ──────────────────────────────────────────────
    COLLEGE_DEPOT_LAT: float = 10.95488   # VSB Engineering College, Karudayampalayam
    COLLEGE_DEPOT_LON: float = 77.95462   # NH-67 Covai Road, Karur 639111
    COLLEGE_NAME: str = "VSB Engineering College, Karudayampalayam, Karur"

    # ─── Fleet & Operating Parameters ─────────────────────────────────────────
    TOTAL_FLEET_SIZE: int = 50
    DEFAULT_BUS_CAPACITY: int = 55
    FIRST_CLASS_ARRIVAL_TIME: str = "08:30"
    # No bus may depart before this. Backward scheduling from
    # FIRST_CLASS_ARRIVAL_TIME subtracts real segment durations; without a floor
    # a slow OSRM duration matrix pushes the first pickup before midnight.
    EARLIEST_ROUTE_DEPARTURE: str = "06:00"

    # Dwell assumptions used only by the heuristic CVRP fallback (used when
    # OR-Tools returns no feasible solution), so its itinerary stays well-formed.
    FALLBACK_DEPOT_DWELL_MINUTES: int = 30
    FALLBACK_STOP_DWELL_MINUTES: int = 3

    # ─── OSRM Routing Engine ───────────────────────────────────────────────────
    # Point to self-hosted OSRM container in production (see docker-compose.yml).
    # Use http://osrm:5000 inside docker-compose network.
    OSRM_BASE_URL: str = Field(
        default="http://osrm:5000",
        description="OSRM HTTP API base URL. Must be self-hosted in production.",
    )
    # DISABLED: straight-line fallback produces wrong route polylines.
    # Enable ONLY temporarily during OSRM container cold-start or local dev.
    ENABLE_OFFLINE_HAVERSINE_FALLBACK: bool = False
    OSRM_REQUEST_TIMEOUT_SECONDS: float = 5.0
    OSRM_MAX_RETRIES: int = 3

    ROAD_DETOUR_INDEX: float = 1.32   # Karur urban-suburban road curvature multiplier
    AVERAGE_BUS_SPEED_KMH: float = 34.0  # Realistic average incl. traffic and stops

    # ─── OR-Tools Optimisation Weights ────────────────────────────────────────
    WEIGHT_STANDING_PENALTY: int = 100
    WEIGHT_EMPTY_SEAT_PENALTY: int = 5
    WEIGHT_CHURN_PENALTY: int = 15

    # ─── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated allowed origins. Never use "*" in production.
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins.",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


settings = Settings()


