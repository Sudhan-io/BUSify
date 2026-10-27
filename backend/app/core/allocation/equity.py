import math
from typing import Dict, Any, Optional, List

def compute_seating_equity(area_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes per-area seat utilization, cross-area utilization variance, and seat-utilization consistency.

    Domain Definition (resolving DATA-003):
    1. Area: An operational transit corridor (e.g. AREA_A through AREA_E).
    2. Area Demand: Total assigned commuter riders across routes serving that area.
    3. Area Capacity: Total seat capacity across physical buses allocated to that area.
    4. Area Utilization: u_i = riders_i / capacity_i (for valid areas where capacity_i > 0 and riders_i >= 0).
    5. Population Variance: sigma^2 = (1/N) * sum((u_i - mean_u)^2).
    6. Coefficient of Variation (CV): CV = sigma / mean_u (defined only when mean_u > 0).
    7. Consistency / Seating Equity: max(0.0, 1.0 - CV) * 100.0, rounded to 1 decimal place.

    Edge-case & Semantic Rules:
    - Invalid/Missing Data: Areas with non-positive capacity, negative demand, or non-numeric/missing values
      are excluded from the comparison population.
    - Duplicate Vehicles / Allocations: If bus-level allocations are provided in an area metric ("buses"),
      capacity is deduplicated by bus_id / bus_code so a single vehicle assigned to multiple route segments
      does not inflate area seat capacity.
    - Empty Dataset (N == 0): No valid measured areas with positive capacity. Variance is None,
      seating_equity_pct is None, status is "UNAVAILABLE".
    - Single Valid Area (N == 1): Cross-area comparison requires at least 2 distinct areas (N >= 2).
      A single area cannot establish cross-corridor consistency. Variance is None, seating_equity_pct is None,
      status is "INSUFFICIENT_AREAS".
    - Zero Demand Across All Areas (mean_u == 0.0): Every measured area has 0 riders. CV is mathematically
      undefined (0/0), and empty buses provide no empirical basis for seat equity or fair access.
      Variance is 0.0, seating_equity_pct is None, status is "ZERO_DEMAND".
    - Non-Zero Demand Across Multiple Valid Areas (N >= 2, mean_u > 0.0): Variance, CV, and seating_equity_pct
      are computed deterministically. Equal utilization yields variance 0.0 and consistency 100.0%. Status is "VALID".

    Args:
        area_metrics: Mapping of area_id -> {"riders": int/float, "capacity": int/float, ...}

    Returns:
        dict containing:
            - seating_equity_pct: Optional[float] (0.0 to 100.0 or None if unavailable/undefined)
            - area_utilization_variance: Optional[float] (population variance or None)
            - area_utilization_std: Optional[float] (population standard deviation or None)
            - mean_area_utilization_pct: Optional[float] (mean area utilization % or None)
            - measured_areas_count: int (number of valid measured areas with capacity > 0)
            - per_area_utilization_pct: dict[str, float] (area_id -> utilization %)
            - equity_status: str ("VALID", "ZERO_DEMAND", "INSUFFICIENT_AREAS", "UNAVAILABLE")
    """
    if not area_metrics or not isinstance(area_metrics, dict):
        return {
            "seating_equity_pct": None,
            "area_utilization_variance": None,
            "area_utilization_std": None,
            "mean_area_utilization_pct": None,
            "measured_areas_count": 0,
            "per_area_utilization_pct": {},
            "equity_status": "UNAVAILABLE",
        }

    valid_utilizations = {}
    for area_id, metrics in area_metrics.items():
        if not isinstance(metrics, dict):
            continue

        # Check for nested bus allocations and deduplicate by vehicle identifier
        buses = metrics.get("buses")
        if isinstance(buses, list):
            seen_buses = set()
            cap_val = 0.0
            for b in buses:
                if isinstance(b, dict):
                    b_id = b.get("bus_id") or b.get("bus_code")
                    seats = b.get("seats", b.get("capacity", 0))
                    try:
                        seats_f = float(seats or 0)
                    except (ValueError, TypeError):
                        seats_f = 0.0

                    if b_id:
                        if b_id not in seen_buses:
                            seen_buses.add(b_id)
                            cap_val += seats_f
                    else:
                        cap_val += seats_f
        else:
            try:
                cap_val = float(metrics.get("capacity") or 0)
            except (ValueError, TypeError):
                cap_val = 0.0

        try:
            raw_riders = metrics.get("riders")
            riders_val = float(0.0 if raw_riders is None else raw_riders)
        except (ValueError, TypeError):
            riders_val = -1.0  # Invalid non-numeric rider count

        # Area is valid only if capacity is positive and demand is non-negative
        if cap_val > 0.0 and riders_val >= 0.0:
            util = riders_val / cap_val
            valid_utilizations[area_id] = util

    n = len(valid_utilizations)
    if n == 0:
        return {
            "seating_equity_pct": None,
            "area_utilization_variance": None,
            "area_utilization_std": None,
            "mean_area_utilization_pct": None,
            "measured_areas_count": 0,
            "per_area_utilization_pct": {},
            "equity_status": "UNAVAILABLE",
        }

    per_area_pct = {a: round(u * 100.0, 1) for a, u in valid_utilizations.items()}

    if n == 1:
        only_u = next(iter(valid_utilizations.values()))
        return {
            "seating_equity_pct": None,
            "area_utilization_variance": None,
            "area_utilization_std": None,
            "mean_area_utilization_pct": round(only_u * 100.0, 1),
            "measured_areas_count": 1,
            "per_area_utilization_pct": per_area_pct,
            "equity_status": "INSUFFICIENT_AREAS",
        }

    mean_u = sum(valid_utilizations.values()) / float(n)
    variance = sum((u - mean_u) ** 2 for u in valid_utilizations.values()) / float(n)
    std_dev = math.sqrt(variance)

    if mean_u > 0.0:
        cv = std_dev / mean_u
        equity = max(0.0, 1.0 - cv) * 100.0
        equity_pct = round(equity, 1)
        status = "VALID"
    else:
        # Every measured area has zero demand. Mean is 0.0; CV is undefined (0/0).
        # Empty buses provide no empirical basis for fair access or seat equity.
        equity_pct = None
        status = "ZERO_DEMAND"

    return {
        "seating_equity_pct": equity_pct,
        "area_utilization_variance": round(variance, 6),
        "area_utilization_std": round(std_dev, 6),
        "mean_area_utilization_pct": round(mean_u * 100.0, 1),
        "measured_areas_count": n,
        "per_area_utilization_pct": per_area_pct,
        "equity_status": status,
    }
