from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.calendar import Calendar
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.data.synthetic_generator import AREAS_CONFIG
from backend.app.schemas import ForecastResponse, AreaForecastItem

router = APIRouter(tags=["Demand Forecasting"])

@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    date: str = Query(default=None, description="Target forecast date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Returns LightGBM quantile ridership forecasts (p50 median and p90 peak)
    for all geographic transit areas on the requested date.
    """
    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    # Check if target date has exam flag in calendar
    cal_entry = db.query(Calendar).filter(Calendar.date == target_date).first()
    is_exam = cal_entry.exam_flag if cal_entry else False

    area_items = []
    for a_id in AREAS_CONFIG.keys():
        pred = forecaster.predict_for_date(target_date, a_id, exam_flag=is_exam)
        area_items.append(AreaForecastItem(
            area_id=a_id,
            date=target_date,
            p50_demand=pred["p50_demand"],
            p90_demand=pred["p90_demand"]
        ))

    total_p50 = sum(item.p50_demand for item in area_items)
    total_p90 = sum(item.p90_demand for item in area_items)

    return ForecastResponse(
        date=target_date,
        is_exam_day=is_exam,
        areas=area_items,
        total_p50_demand=total_p50,
        total_p90_demand=total_p90
    )
