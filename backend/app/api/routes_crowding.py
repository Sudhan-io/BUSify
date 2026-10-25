from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.bus import Bus
from backend.app.models.calendar import Calendar
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.simulation.simulator import BASELINE_ALLOCATION
from backend.app.core.data.synthetic_generator import AREAS_CONFIG

router = APIRouter(tags=["Student Crowding"])

@router.get("/crowding")
def get_bus_crowding(
    bus_id: str = Query(..., description="Target vehicle ID (e.g. BUS-01, BUS-14)"),
    date: str = Query(default=None, description="Date for crowd estimate (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Returns real-time and predicted crowd congestion indicators for a specific bus:
    - Crowd Status: Low (< 70%), Moderate (70-90%), High (90-100%), Overcrowded (> 100%)
    - Utilization Percentage
    - Assigned Zone and pickup timings
    """
    bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail=f"Bus '{bus_id}' not found in fleet.")

    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    cal_entry = db.query(Calendar).filter(Calendar.date == target_date).first()
    is_exam = cal_entry.exam_flag if cal_entry else False

    # Get assigned area (either dynamic allocation or default)
    assigned_area = bus.default_area_id or "AREA_A"

    # Defensive: buses seeded before area validation existed may carry an area
    # the forecaster was never trained on, which would raise inside the encoder.
    if assigned_area not in AREAS_CONFIG:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Bus '{bus_id}' is assigned to unknown area '{assigned_area}'. "
                f"Valid areas: {sorted(AREAS_CONFIG.keys())}"
            ),
        )

    # Compute forecast for this area
    pred = forecaster.predict_for_date(target_date, assigned_area, exam_flag=is_exam)
    p50_area = pred["p50_demand"]
    p90_area = pred["p90_demand"]

    # Solve allocation to see how many buses are serving this area
    all_demands = {
        a: forecaster.predict_for_date(target_date, a, exam_flag=is_exam)["p90_demand"]
        for a in AREAS_CONFIG.keys()
    }
    alloc_res = fleet_allocator.solve(all_demands, BASELINE_ALLOCATION)
    buses_in_area = alloc_res["allocation"].get(assigned_area, 8)

    # Average load per bus in this area
    avg_passengers_p50 = round(p50_area / max(buses_in_area, 1), 1)
    avg_passengers_p90 = round(p90_area / max(buses_in_area, 1), 1)
    utilization_pct = round((avg_passengers_p90 / bus.seats) * 100, 1)

    if utilization_pct <= 70.0:
        crowd_level = "LOW"
        crowd_color = "emerald"
        message = "Ample seats available. Comfortable travel expected."
    elif utilization_pct <= 90.0:
        crowd_level = "MODERATE"
        crowd_color = "amber"
        message = "Normal ridership. Most seats will be occupied."
    elif utilization_pct <= 100.0:
        crowd_level = "BUSY"
        crowd_color = "orange"
        message = "High volume. Arrive early at your designated stop."
    else:
        crowd_level = "OVERCROWDED"
        crowd_color = "rose"
        message = "Standing passengers expected due to morning demand peak."

    return {
        "bus_id": bus.bus_id,
        "date": target_date,
        "seats_capacity": bus.seats,
        "assigned_area_id": assigned_area,
        "area_name": AREAS_CONFIG.get(assigned_area, {}).get("name", assigned_area),
        "crowd_level": crowd_level,
        "crowd_badge_color": crowd_color,
        "utilization_pct": utilization_pct,
        "expected_riders_p50": int(round(avg_passengers_p50)),
        "expected_riders_p90": int(round(avg_passengers_p90)),
        "advisory_message": message
    }
