from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.calendar import Calendar
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.data.synthetic_generator import AREAS_CONFIG
from backend.app.core.simulation.simulator import BASELINE_ALLOCATION
from backend.app.schemas import AllocationResponse

router = APIRouter(tags=["Fleet Allocation"])

@router.get("/allocation", response_model=AllocationResponse)
def get_fleet_allocation(
    date: str = Query(default=None, description="Target optimization date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Computes optimal fleet distribution across areas using OR-Tools CP-SAT
    against predicted p90 demand on the specified date.
    """
    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    cal_entry = db.query(Calendar).filter(Calendar.date == target_date).first()
    is_exam = cal_entry.exam_flag if cal_entry else False

    # 1. Forecast p90 demands
    predicted_demands = {}
    for a_id in AREAS_CONFIG.keys():
        pred = forecaster.predict_for_date(target_date, a_id, exam_flag=is_exam)
        predicted_demands[a_id] = pred["p90_demand"]

    # 2. Solve CP-SAT integer program
    result = fleet_allocator.solve(
        predicted_demands=predicted_demands,
        current_allocations=BASELINE_ALLOCATION
    )

    return AllocationResponse(
        date=target_date,
        status=result["status"],
        total_fleet_available=result["total_fleet_available"],
        total_buses_allocated=result["total_buses_allocated"],
        baseline_allocation=BASELINE_ALLOCATION,
        optimized_allocation=result["allocation"],
        metrics=result["metrics"],
        per_area_details=result["per_area_details"]
    )
