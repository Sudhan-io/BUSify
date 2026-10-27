import math
from typing import Dict, Any

def compute_seating_equity(area_metrics: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """
    Computes per-area utilization, cross-area utilization variance, and seating equity percentage.

    Domain Definition (resolving DATA-003):
    1. Area: An operational transit corridor (e.g. AREA_A through AREA_E).
    2. Area Demand: Total assigned commuter riders across routes serving that area.
    3. Area Capacity: Total seat capacity across all dispatched buses allocated to that area.
    4. Area Utilization: u_i = riders_i / capacity_i (for areas where capacity_i > 0).
    5. Utilization Variance: Population variance sigma^2 = (1/N) * sum((u_i - mean_u)^2).
    6. Coefficient of Variation (CV): CV = sigma / mean_u (or 0.0 if mean_u == 0.0).
    7. Seating Equity: max(0.0, 1.0 - CV) * 100.0, rounded to 1 decimal place.

    Edge-case Handling:
    - Areas with capacity == 0 are excluded from utilization division to prevent division-by-zero.
    - If no areas have capacity > 0 (N == 0), returns variance 0.0, CV 0.0, equity 0.0%.
    - If only 1 area has capacity > 0 (N == 1), variance is 0.0, CV 0.0, equity 100.0%.
    - If all measured areas have equal utilization, variance is 0.0, CV 0.0, equity 100.0%.

    Args:
        area_metrics: Mapping of area_id -> {"riders": int, "capacity": int}

    Returns:
        dict containing:
            - seating_equity_pct: float (0.0 to 100.0)
            - area_utilization_variance: float (dimensionless population variance)
            - area_utilization_std: float (population standard deviation)
            - mean_area_utilization_pct: float (mean area utilization percentage)
            - measured_areas_count: int (number of valid measured areas with capacity > 0)
            - per_area_utilization_pct: dict[str, float] (area_id -> utilization %)
    """
    if not area_metrics:
        return {
            "seating_equity_pct": 0.0,
            "area_utilization_variance": 0.0,
            "area_utilization_std": 0.0,
            "mean_area_utilization_pct": 0.0,
            "measured_areas_count": 0,
            "per_area_utilization_pct": {},
        }

    valid_utilizations = {}
    for area_id, metrics in area_metrics.items():
        cap = metrics.get("capacity", 0)
        riders = metrics.get("riders", 0)
        if cap > 0 and riders is not None:
            util = riders / float(cap)
            valid_utilizations[area_id] = util

    n = len(valid_utilizations)
    if n == 0:
        return {
            "seating_equity_pct": 0.0,
            "area_utilization_variance": 0.0,
            "area_utilization_std": 0.0,
            "mean_area_utilization_pct": 0.0,
            "measured_areas_count": 0,
            "per_area_utilization_pct": {},
        }

    per_area_pct = {a: round(u * 100.0, 1) for a, u in valid_utilizations.items()}

    if n == 1:
        only_u = next(iter(valid_utilizations.values()))
        return {
            "seating_equity_pct": 100.0,
            "area_utilization_variance": 0.0,
            "area_utilization_std": 0.0,
            "mean_area_utilization_pct": round(only_u * 100.0, 1),
            "measured_areas_count": 1,
            "per_area_utilization_pct": per_area_pct,
        }

    mean_u = sum(valid_utilizations.values()) / float(n)
    variance = sum((u - mean_u) ** 2 for u in valid_utilizations.values()) / float(n)
    std_dev = math.sqrt(variance)

    if mean_u > 0.0:
        cv = std_dev / mean_u
        equity = max(0.0, 1.0 - cv) * 100.0
    else:
        # All areas have 0.0 utilization (perfect equality at zero load)
        cv = 0.0
        equity = 100.0

    return {
        "seating_equity_pct": round(equity, 1),
        "area_utilization_variance": round(variance, 6),
        "area_utilization_std": round(std_dev, 6),
        "mean_area_utilization_pct": round(mean_u * 100.0, 1),
        "measured_areas_count": n,
        "per_area_utilization_pct": per_area_pct,
    }
