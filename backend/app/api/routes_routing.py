from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.calendar import Calendar
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.forecasting.disaggregator import disaggregate_area_demand
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.routing.vrp_solver import vrp_solver
from backend.app.core.simulation.simulator import BASELINE_ALLOCATION
from backend.app.core.data.synthetic_generator import AREAS_CONFIG

router = APIRouter(tags=["Vehicle Routing"])

@router.get("/routes")
def get_area_routes(
    area_id: str = Query(..., description="Target transit zone (e.g. AREA_A, AREA_B)"),
    date: str = Query(default=None, description="Date for route plan (YYYY-MM-DD)"),
    campus_lat: float = Query(default=None, description="Campus hub depot latitude"),
    campus_lng: float = Query(default=None, description="Campus hub depot longitude"),
    direction: str = Query(default="MORNING_PICKUP", description="MORNING_PICKUP or EVENING_DROP"),
    db: Session = Depends(get_db)
):
    """
    Computes capacitated vehicle routes and backward-scheduled stop itineraries
    for the allocated buses in the selected area. Supports custom campus depot and morning/evening directions.
    """
    if area_id not in AREAS_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid area_id '{area_id}'. Available: {list(AREAS_CONFIG.keys())}")

    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    cal_entry = db.query(Calendar).filter(Calendar.date == target_date).first()
    is_exam = cal_entry.exam_flag if cal_entry else False

    # 1. Forecast p50 and p90 for this area
    area_forecast = forecaster.predict_for_date(target_date, area_id, exam_flag=is_exam)

    # 2. Get fleet allocation for this area
    all_demands = {
        a: forecaster.predict_for_date(target_date, a, exam_flag=is_exam)["p90_demand"]
        for a in AREAS_CONFIG.keys()
    }
    alloc_res = fleet_allocator.solve(all_demands, BASELINE_ALLOCATION)
    buses_for_area = alloc_res["allocation"].get(area_id, 8)

    # 3. Disaggregate demand to stops
    stops = disaggregate_area_demand(
        area_id=area_id,
        area_p50=area_forecast["p50_demand"],
        area_p90=area_forecast["p90_demand"]
    )

    college_depot = (campus_lat, campus_lng) if (campus_lat is not None and campus_lng is not None) else None

    # 4. Solve Capacitated VRP
    routing_result = vrp_solver.solve(
        area_id=area_id,
        stops=stops,
        num_buses=buses_for_area,
        college_depot=college_depot,
        direction=direction
    )

    return routing_result
