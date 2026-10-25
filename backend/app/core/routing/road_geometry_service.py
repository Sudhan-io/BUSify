"""
road_geometry_service.py — OSRM-backed real road polyline fetcher.

Queries a self-hosted OSRM instance to return turn-by-turn road geometries
for bus route polylines. Uses connection retries with exponential back-off.

FALLBACK POLICY:
    ENABLE_OFFLINE_HAVERSINE_FALLBACK must be explicitly True in .env to allow
    straight-line fallback. Default is False — routes that cannot be road-snapped
    will raise a structured error rather than silently produce wrong polylines.
"""

import logging
import time
from typing import List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.app.config import settings

logger = logging.getLogger(__name__)


def _build_osrm_session() -> requests.Session:
    """
    Builds a requests.Session with automatic retry on transient HTTP/network errors.
    Retries on connection errors and 5xx responses with exponential back-off.
    """
    session = requests.Session()
    retry = Retry(
        total=settings.OSRM_MAX_RETRIES,
        backoff_factor=0.5,          # waits 0.5s, 1.0s, 2.0s between retries
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Module-level session reuse across requests (connection pooling)
_osrm_session = _build_osrm_session()


class RoadGeometryService:
    """
    Fetches real-world turn-by-turn road polyline geometries from a self-hosted
    OSRM instance. Ensures bus route polylines strictly follow actual roads,
    streets, highways, and bridges instead of cutting straight lines.

    Configuration:
        OSRM_BASE_URL                    — Self-hosted OSRM server URL
        OSRM_REQUEST_TIMEOUT_SECONDS     — Per-request timeout (default: 5s)
        ENABLE_OFFLINE_HAVERSINE_FALLBACK — Must be True to allow straight-line fallback
    """

    def __init__(self):
        self._cache: dict = {}

    def get_road_geometry(
        self, waypoints: List[Tuple[float, float]]
    ) -> List[List[float]]:
        """
        Fetches OSRM road-snapped polyline for a list of waypoints.

        Args:
            waypoints: List of (lat, lon) tuples or dicts with lat/lon keys.

        Returns:
            List of [lat, lon] pairs following the actual road network.

        Raises:
            RuntimeError: If OSRM is unreachable AND haversine fallback is disabled.
        """
        if not waypoints or len(waypoints) < 2:
            return []

        # Normalise heterogeneous input formats
        norm_waypoints: List[Tuple[float, float]] = []
        for wp in waypoints:
            if isinstance(wp, dict):
                lat = wp.get("lat") or wp.get("latitude")
                lon = wp.get("lon") or wp.get("lng") or wp.get("longitude")
                if lat is not None and lon is not None:
                    norm_waypoints.append((float(lat), float(lon)))
            elif isinstance(wp, (list, tuple)) and len(wp) >= 2:
                norm_waypoints.append((float(wp[0]), float(wp[1])))

        if len(norm_waypoints) < 2:
            return [[lat, lon] for lat, lon in norm_waypoints]

        # Cache key on rounded coordinates (5 decimal places ≈ 1.1 m precision)
        cache_key = tuple((round(lat, 5), round(lon, 5)) for lat, lon in norm_waypoints)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # ── OSRM query ───────────────────────────────────────────────────────
        # OSRM coordinate format: lon,lat (note: reversed from Leaflet's lat,lon)
        coords_str = ";".join(
            f"{lon:.6f},{lat:.6f}" for lat, lon in norm_waypoints
        )
        url = (
            f"{settings.OSRM_BASE_URL}/route/v1/driving/{coords_str}"
            f"?overview=full&geometries=geojson"
        )

        try:
            resp = _osrm_session.get(
                url, timeout=settings.OSRM_REQUEST_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == "Ok" and data.get("routes"):
                # OSRM GeoJSON coords are [lon, lat]; Leaflet needs [lat, lon]
                geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                leaflet_coords = [[lat, lon] for lon, lat in geojson_coords]
                if leaflet_coords:
                    self._cache[cache_key] = leaflet_coords
                    return leaflet_coords

            logger.warning(
                "OSRM returned unexpected response (code=%s) for %d waypoints.",
                data.get("code"),
                len(norm_waypoints),
            )

        except requests.exceptions.Timeout:
            logger.error(
                "OSRM request timed out after %.1fs for %d waypoints. URL: %s",
                settings.OSRM_REQUEST_TIMEOUT_SECONDS,
                len(norm_waypoints),
                url,
            )
        except requests.exceptions.ConnectionError:
            logger.error(
                "Cannot reach OSRM server at %s. Is the OSRM container running?",
                settings.OSRM_BASE_URL,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("OSRM request failed: %s", exc)

        # ── Fallback policy ──────────────────────────────────────────────────
        if settings.ENABLE_OFFLINE_HAVERSINE_FALLBACK:
            logger.warning(
                "Using straight-line coordinate fallback for %d waypoints. "
                "Route polylines will NOT follow actual roads. "
                "Set ENABLE_OFFLINE_HAVERSINE_FALLBACK=False to enforce OSRM.",
                len(norm_waypoints),
            )
            fallback = [[lat, lon] for lat, lon in norm_waypoints]
            self._cache[cache_key] = fallback
            return fallback

        # Fallback disabled — raise so callers know routing failed
        raise RuntimeError(
            f"OSRM road geometry unavailable for {len(norm_waypoints)} waypoints "
            f"and ENABLE_OFFLINE_HAVERSINE_FALLBACK is False. "
            f"Check that the OSRM container is running at {settings.OSRM_BASE_URL}."
        )


road_geometry_service = RoadGeometryService()

