import pandas as pd
from sqlalchemy import text
from backend.app.database import engine

def get_stop_weights_for_area(area_id: str) -> list[dict]:
    """
    Computes the proportional registration share for each stop within a given area.
    """
    query = """
    SELECT 
        s.stop_id,
        s.name,
        s.lat,
        s.lon,
        s.sequence_order,
        COUNT(r.reg_id) as registered_count
    FROM stops s
    LEFT JOIN registrations r ON s.stop_id = r.stop_id
    WHERE s.area_id = :area_id
    GROUP BY s.stop_id, s.name, s.lat, s.lon, s.sequence_order
    ORDER BY s.sequence_order ASC
    """
    df = pd.read_sql(text(query), con=engine, params={"area_id": area_id})
    total_area_regs = df["registered_count"].sum()
    
    if total_area_regs == 0:
        df["weight"] = 1.0 / len(df) if len(df) > 0 else 0
    else:
        df["weight"] = df["registered_count"] / total_area_regs

    return df.to_dict(orient="records")

def disaggregate_area_demand(area_id: str, area_p50: int, area_p90: int) -> list[dict]:
    """
    Distributes area-level quantile demand forecasts down to each stop
    proportionately to its registered student base.
    """
    stops = get_stop_weights_for_area(area_id)
    results = []
    
    remaining_p50 = area_p50
    remaining_p90 = area_p90

    for i, s in enumerate(stops):
        # Round share of demand
        if i == len(stops) - 1:
            stop_p50 = max(0, remaining_p50)
            stop_p90 = max(stop_p50, remaining_p90)
        else:
            stop_p50 = int(round(area_p50 * s["weight"]))
            stop_p90 = int(round(area_p90 * s["weight"]))
            remaining_p50 -= stop_p50
            remaining_p90 -= stop_p90
            
        results.append({
            "stop_id": s["stop_id"],
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "area_id": area_id,
            "registered_count": s["registered_count"],
            "p50_riders": stop_p50,
            "p90_riders": max(stop_p90, stop_p50),
        })

    return results
