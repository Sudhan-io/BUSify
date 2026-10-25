"""
matrix_service.py — Distance/duration matrix provider for the CVRP solver.

FALLBACK POLICY (mirrors road_geometry_service):
    Live OSRM is always attempted first. If it fails, straight-line Haversine
    distances are used ONLY when ENABLE_OFFLINE_HAVERSINE_FALLBACK is explicitly
    True. Otherwise a RuntimeError is raised.

This matters because the solver optimises against this matrix while the map
draws real road geometry: silently degrading to straight-line distances produces
routes that look correct on screen but are not the routes that were optimised.
"""

from __future__ import annotations

import logging
import math

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.app.config import settings

logger = logging.getLogger(__name__)

# The matrix is derived from a small, bounded coordinate set, so a generous cap
# is safe and prevents unbounded cache growth in long-lived workers.
MATRIX_CACHE_MAX_ENTRIES = 64


def _build_osrm_session() -> requests.Session:
    """Session with retry on transient connection/5xx errors (pooled across calls)."""
    session = requests.Session()
    retry = Retry(
        total=settings.OSRM_MAX_RETRIES,
        backoff_factor=0.5,          # waits 0.5s, 1.0s, 2.0s between retries
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_osrm_session = _build_osrm_session()


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates in meters.
    """
    R = 6371000  # Radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class DistanceMatrixService:
    """
    Computes distance and duration matrices between transit nodes.
    Prefers live OSRM table queries; falls back to calibrated geodesic Haversine
    distances scaled by the road-detour index only when explicitly permitted.
    """

    def __init__(self):
        self._cache: dict = {}

    def get_matrices(self, coordinates: list[tuple[float, float]]) -> tuple[list[list[int]], list[list[int]]]:
        """
        Calculates NxN distance (meters) and duration (seconds) matrices.
        Coordinates list is [(lat, lon), ...].

        Raises:
            RuntimeError: if OSRM is unreachable AND haversine fallback is disabled.
        """
        n = len(coordinates)
        if n == 0:
            return [], []

        # Round to 5dp (~1.1 m) so trivially different float tails share a cache entry.
        cache_key = tuple((round(lat, 5), round(lon, 5)) for lat, lon in coordinates)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        matrices = self._fetch_osrm_matrices(coordinates, cache_key)
        if matrices is None:
            matrices = self._haversine_matrices(coordinates)
            if not settings.ENABLE_OFFLINE_HAVERSINE_FALLBACK:
                raise RuntimeError(
                    f"OSRM distance matrix unavailable for {n} coordinates and "
                    f"ENABLE_OFFLINE_HAVERSINE_FALLBACK is False. Check that the "
                    f"OSRM container is running at {settings.OSRM_BASE_URL}."
                )

        self._store(cache_key, matrices)
        return matrices

    # ── OSRM path ───────────────────────────────────────────────────────────
    def _fetch_osrm_matrices(
        self,
        coordinates: list[tuple[float, float]],
        cache_key: tuple,
    ) -> tuple[list[list[int]], list[list[int]]] | None:
        """
        Queries the OSRM /table endpoint. Returns None on any failure so the
        caller can apply the configured fallback policy — the failure reason is
        logged here rather than swallowed.
        """
        coords_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coordinates)
        url = (
            f"{settings.OSRM_BASE_URL}/table/v1/driving/{coords_str}"
            f"?annotations=distance,duration"
        )

        try:
            resp = _osrm_session.get(
                url, timeout=settings.OSRM_REQUEST_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            data = resp.json()
            if "distances" in data and "durations" in data:
                dist_matrix = [[int(d) for d in row] for row in data["distances"]]
                dur_matrix = [[int(t) for t in row] for row in data["durations"]]
                return dist_matrix, dur_matrix
            logger.error(
                "OSRM /table response missing distances/durations for %d nodes (code=%s).",
                len(coordinates),
                data.get("code"),
            )
        except requests.exceptions.Timeout:
            logger.error(
                "OSRM /table timed out after %.1fs for %d nodes.",
                settings.OSRM_REQUEST_TIMEOUT_SECONDS,
                len(coordinates),
            )
        except requests.exceptions.ConnectionError:
            logger.error(
                "Cannot reach OSRM at %s for /table. Is the OSRM container running?",
                settings.OSRM_BASE_URL,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("OSRM /table request failed: %s", exc)
        except ValueError as exc:
            logger.error("OSRM /table returned a non-JSON body: %s", exc)

        return None

    # ── Haversine path ──────────────────────────────────────────────────────
    def _haversine_matrices(
        self, coordinates: list[tuple[float, float]]
    ) -> tuple[list[list[int]], list[list[int]]]:
        """Geodesic fallback with an empirical road-detour factor."""
        n = len(coordinates)
        detour = settings.ROAD_DETOUR_INDEX
        speed_mps = (settings.AVERAGE_BUS_SPEED_KMH * 1000.0) / 3600.0

        logger.warning(
            "Using straight-line Haversine distances for %d nodes. The CVRP will "
            "optimise against an approximation of the road network.",
            n,
        )

        distance_matrix = []
        duration_matrix = []

        for i in range(n):
            dist_row = []
            dur_row = []
            lat1, lon1 = coordinates[i]
            for j in range(n):
                if i == j:
                    dist_row.append(0)
                    dur_row.append(0)
                else:
                    lat2, lon2 = coordinates[j]
                    crow_flies = haversine_distance_meters(lat1, lon1, lat2, lon2)
                    road_dist = int(round(crow_flies * detour))
                    transit_duration = int(round(road_dist / speed_mps))
                    dist_row.append(road_dist)
                    dur_row.append(transit_duration)
            distance_matrix.append(dist_row)
            duration_matrix.append(dur_row)

        return distance_matrix, duration_matrix

    # ── cache ───────────────────────────────────────────────────────────────
    def _store(self, cache_key: tuple, matrices: tuple) -> None:
        if len(self._cache) >= MATRIX_CACHE_MAX_ENTRIES:
            # dict preserves insertion order; evict the oldest entry.
            self._cache.pop(next(iter(self._cache)), None)
        self._cache[cache_key] = matrices


matrix_service = DistanceMatrixService()